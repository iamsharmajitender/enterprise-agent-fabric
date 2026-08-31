import json
from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.prefetch import (
    PREFETCH_SLOT_ID,
    PrefetchPort,
    is_prefetch_stage,
    prefetch_corpus_stage_id,
    prefetch_pack_text,
    require_prefetch_pack,
    run_prefetch,
)
from app.agents.jobs_client import JobsPort
from app.graph.branch import branch_slot_key, resolve_branch_target
from app.graph.customer_ask import CustomerAskWaiting
from app.graph.human_gate import (
    HumanGateWaiting,
    gate_packet_present,
    human_gate_slot_key,
    resume_index_after_gate,
)
from app.graph.subagent_gate import (
    SubagentWaiting,
    join_enabled,
    subagent_result_present,
)
from app.graph.llm import LlmPort
from app.graph.llm.schema import llm_output_schema
from app.graph.payload import (
    merge_http_payload,
    parse_llm_slot,
    project_child_goal,
    project_slot,
    validate_input_schema,
)
from app import telemetry
from app.tools.invoker import ToolInvoker


class GraphState(TypedDict, total=False):
    result: str
    goal: dict[str, Any]
    notes: list[str]
    slots: dict[str, Any]
    correlation_id: str


# Catalogue llm_role values: none (HTTP), query_formulation (LLM then HTTP),
# classify/synthesis (LLM, skip HTTP).
_LLM_ONLY_ROLES = frozenset({"classify", "synthesis"})
_KNOWN_LLM_ROLES = frozenset({"none", "query_formulation"}) | _LLM_ONLY_ROLES


def _stage_key(tool: dict[str, Any]) -> str:
    """Workflow stage id used for branch targets and routing."""
    return str(tool.get("workflow_stage_id") or tool.get("id") or "")


def _expects_prefetch_pack(tools: list[dict[str, Any]]) -> bool:
    """True when the hydrated workflow includes a prefetch placeholder stage."""
    return any(str(tool.get("id") or "") == PREFETCH_SLOT_ID for tool in tools)


def _node_name(tool: dict[str, Any], index: int) -> str:
    """LangGraph node id from capability id plus stage index."""
    raw = str(tool.get("id") or f"tool_{index}")
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in raw)
    return f"{cleaned}_{index}"


def _message(body: dict[str, Any]) -> str:
    """Pull a human-readable string from a tool HTTP body."""
    text = str(body.get("text") or body.get("message") or "").strip()
    if text:
        return text
    order_id = str(body.get("order_id") or "").strip()
    if order_id:
        item = str(body.get("item_name") or body.get("item_id") or "item").strip()
        price = body.get("price")
        if price is not None:
            return f"Order {order_id}: {item} ${price:g}."
        return f"Order {order_id}: {item}."
    return ""


def _user_blob(goal: dict[str, Any], notes: list[str], slots: dict[str, Any] | None = None) -> str:
    """Build the LLM user message from the goal, prefetch pack, and prior stage notes."""
    lines = [f"goal: {goal}"]
    pack = prefetch_pack_text(slots)
    if pack:
        lines.append("packed chunks:")
        lines.extend(f"- {line}" for line in pack.splitlines())
    if notes:
        lines.append("prior stage outputs:")
        lines.extend(f"- {note}" for note in notes)
    return "\n".join(lines)


def _llm_role(raw: Any) -> str:
    """Normalize llm_role; reject values the graph does not implement."""
    role = str(raw or "none").strip() or "none"
    if role not in _KNOWN_LLM_ROLES:
        raise RuntimeError(f"unknown llm_role {role!r}")
    return role


def _mapping(value: Any) -> dict[str, Any]:
    """Treat a non-dict as empty so stage fields stay optional."""
    return value if isinstance(value, dict) else {}


def _slots(state: GraphState) -> dict[str, Any]:
    """Copy prior stage slots from graph state."""
    raw = state.get("slots")
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


def _stage_id(pinned: dict[str, Any]) -> str:
    """Stable slot key for a hydrated capability."""
    return str(pinned.get("id") or "")


def _write_slot(
    slots: dict[str, Any],
    stage_id: str,
    body: dict[str, Any],
    pinned: dict[str, Any],
) -> dict[str, Any]:
    """Persist one stage output into the in-run slot map."""
    if not stage_id:
        return slots
    schema = pinned.get("output_schema") if isinstance(pinned.get("output_schema"), dict) else None
    updated = dict(slots)
    updated[stage_id] = project_slot(body, schema)
    return updated


def _llm_complete(
    llm: LlmPort,
    prompt: str,
    user: str,
    pinned: dict[str, Any],
    role: str,
) -> str:
    """Complete with capability output_schema when the stage is an LLM call."""
    schema = llm_output_schema(pinned, role)
    if schema is not None:
        return llm.complete(prompt, user, schema=schema)
    return llm.complete(prompt, user)


def _stage_request_preview(
    pinned: dict[str, Any],
    goal: dict[str, Any],
    notes: list[str],
    slots: dict[str, Any],
    input_schema: dict[str, Any] | None,
    role: str,
    retrieval: dict[str, Any] | None,
    call_args: dict[str, Any] | None,
) -> Any:
    """Best-effort request body for run.stage.started digests (before side effects)."""
    invoke = _mapping(pinned.get("invoke"))
    if role in _LLM_ONLY_ROLES:
        return _user_blob(goal, notes, slots)
    payload = merge_http_payload(goal, slots, input_schema, call_args)
    if str(pinned.get("kind") or "") == "agent":
        return project_child_goal(goal, slots, input_schema, call_args)
    if is_prefetch_stage(pinned, retrieval):
        return goal
    if not str(invoke.get("url") or "").strip():
        return goal
    return payload


def _run_stage(
    pinned: dict[str, Any],
    state: GraphState,
    invoker: ToolInvoker,
    llm: LlmPort | None,
    *,
    retrieval: dict[str, Any] | None = None,
    prefetch: PrefetchPort | None = None,
    catalogue: Any = None,
    expects_prefetch: bool = False,
    jobs: JobsPort | None = None,
    call_args: dict[str, Any] | None = None,
) -> GraphState:
    """Run one hydrated capability: LLM-only, LLM-then-HTTP, HTTP, or no-op."""
    goal = _mapping(state.get("goal"))
    notes = list(state.get("notes") or [])
    slots = _slots(state)
    stage_id = _stage_id(pinned)
    role = _llm_role(pinned.get("llm_role"))
    input_schema = pinned.get("input_schema") if isinstance(pinned.get("input_schema"), dict) else None
    request_body = _stage_request_preview(
        pinned, goal, notes, slots, input_schema, role, retrieval, call_args
    )
    telemetry.emit_stage_started(stage_id, role, request_body)
    try:
        return _run_stage_impl(
            pinned,
            state,
            invoker,
            llm,
            retrieval=retrieval,
            prefetch=prefetch,
            catalogue=catalogue,
            expects_prefetch=expects_prefetch,
            jobs=jobs,
            call_args=call_args,
        )
    except (HumanGateWaiting, SubagentWaiting, CustomerAskWaiting):
        raise
    except RuntimeError:
        telemetry.emit_stage_failed(stage_id, role, request_body, "runtime_error")
        raise
    except Exception:
        telemetry.emit_stage_failed(stage_id, role, request_body, "stage_error")
        raise


def _run_stage_impl(
    pinned: dict[str, Any],
    state: GraphState,
    invoker: ToolInvoker,
    llm: LlmPort | None,
    *,
    retrieval: dict[str, Any] | None = None,
    prefetch: PrefetchPort | None = None,
    catalogue: Any = None,
    expects_prefetch: bool = False,
    jobs: JobsPort | None = None,
    call_args: dict[str, Any] | None = None,
) -> GraphState:
    """Internal stage runner (telemetry started/failed wraps _run_stage)."""
    invoke = _mapping(pinned.get("invoke"))
    goal = _mapping(state.get("goal"))
    notes = list(state.get("notes") or [])
    slots = _slots(state)
    stage_id = _stage_id(pinned)
    role = _llm_role(pinned.get("llm_role"))
    prompt = str(pinned.get("llm_prompt") or "")
    input_schema = pinned.get("input_schema") if isinstance(pinned.get("input_schema"), dict) else None

    if str(pinned.get("stage_type") or "") == "human_gate":
        gate_id = human_gate_slot_key(pinned)
        if gate_packet_present(slots, gate_id):
            return {"result": str(state.get("result") or ""), "notes": notes, "slots": slots}
        raise HumanGateWaiting(
            stage_id=gate_id,
            gate_index=int(pinned.get("_graph_index") or 0),
            resume_index=resume_index_after_gate(
                pinned.get("_graph_tools") or [pinned],
                int(pinned.get("_graph_index") or 0),
            ),
            state={
                "result": str(state.get("result") or ""),
                "goal": goal,
                "notes": notes,
                "slots": slots,
            },
        )

    if role in _LLM_ONLY_ROLES:
        if llm is None:
            raise RuntimeError(f"llm required for {role}")
        require_prefetch_pack(slots, retrieval, stage_id, expects_prefetch=expects_prefetch)
        user = _user_blob(goal, notes, slots)
        text = _llm_complete(llm, prompt, user, pinned, role)
        notes.append(text)
        slot_body = parse_llm_slot(text)
        return {
            "result": text,
            "notes": notes,
            "slots": _write_slot(slots, stage_id, slot_body, pinned),
        }
    payload = merge_http_payload(goal, slots, input_schema, call_args)
    if role == "query_formulation":
        if llm is None:
            raise RuntimeError("llm required for query_formulation")
        require_prefetch_pack(slots, retrieval, stage_id, expects_prefetch=expects_prefetch)
        payload["query"] = _llm_complete(
            llm, prompt, _user_blob(goal, notes, slots), pinned, role
        )
    if str(pinned.get("kind") or "") == "agent":
        if jobs is None:
            raise RuntimeError("jobs client required for kind=agent")
        if subagent_result_present(slots, stage_id):
            prior = slots.get(stage_id) if isinstance(slots.get(stage_id), dict) else {}
            text = str((prior or {}).get("result") or state.get("result") or "")
            if isinstance((prior or {}).get("result"), dict):
                text = f"Subagent {(prior or {}).get('status')}: {stage_id}"
            notes.append(text)
            return {"result": text, "notes": notes, "slots": slots}
        child_goal = project_child_goal(goal, slots, input_schema, call_args)
        validate_input_schema(child_goal, input_schema)
        invoke_body = invoke.get("body") if isinstance(invoke.get("body"), dict) else {}
        child_route_id = str(invoke_body.get("route_id") or "")
        if not child_route_id:
            raise RuntimeError("agent invoke missing route_id")
        parent_id = str(state.get("correlation_id") or "")
        idempotency_key = (
            f"subagent-{parent_id}-{stage_id}" if parent_id else f"subagent-{stage_id}"
        )
        started = jobs.start(
            child_route_id,
            idempotency_key,
            child_goal,
            invoke=invoke,
        )
        child_correlation_id = str(started.get("correlation_id") or "")
        text = f"Started subagent {child_route_id} ({child_correlation_id})"
        notes.append(text)
        slot_body = {
            "route_id": child_route_id,
            "correlation_id": child_correlation_id,
            "payload": child_goal,
            "status": "running",
        }
        new_slots = _write_slot(slots, stage_id, slot_body, pinned)
        if join_enabled(pinned, invoke):
            gate_index = int(pinned.get("_graph_index") or 0)
            raise SubagentWaiting(
                stage_id=stage_id,
                gate_index=gate_index,
                resume_index=gate_index + 1,
                subagent_ids=[child_correlation_id],
                state={
                    "result": text,
                    "goal": goal,
                    "notes": notes,
                    "slots": new_slots,
                    "correlation_id": parent_id,
                },
            )
        return {
            "result": text,
            "notes": notes,
            "slots": new_slots,
        }
    url = str(invoke.get("url") or "")
    if not url:
        if is_prefetch_stage(pinned, retrieval):
            if prefetch is None or catalogue is None:
                raise RuntimeError("prefetch client required")
            slot_body, note, per_corpus = run_prefetch(
                catalogue, prefetch, retrieval or {}, goal
            )
            notes.append(note)
            new_slots = _write_slot(slots, stage_id, slot_body, pinned)
            for hit in per_corpus:
                corpus_id = str(hit.get("corpus_id") or "")
                if not corpus_id:
                    continue
                new_slots = {
                    **new_slots,
                    prefetch_corpus_stage_id(corpus_id): {
                        "corpus_id": corpus_id,
                        "chunks": hit.get("chunks") or [],
                    },
                }
            return {
                "result": note,
                "notes": notes,
                "slots": new_slots,
            }
        result = notes[-1] if notes else str(state.get("result") or "")
        return {"result": result, "notes": notes, "slots": slots}
    validate_input_schema(payload, input_schema)
    response = invoker.call(invoke, payload)
    text = _message(response)
    notes.append(text)
    return {
        "result": text,
        "notes": notes,
        "slots": _write_slot(slots, stage_id, response, pinned),
    }


def _branch_index(tools: list[dict[str, Any]]) -> int | None:
    """Index of the first stage that declares a branch map, if any."""
    for index, tool in enumerate(tools):
        branch = tool.get("branch")
        if isinstance(branch, dict) and branch:
            return index
    return None


def _make_stage_node(
    name: str,
    tool: dict[str, Any],
    index: int,
    invoker: ToolInvoker,
    llm: LlmPort | None,
    *,
    retrieval: dict[str, Any] | None,
    prefetch: PrefetchPort | None,
    catalogue: Any,
    expects_prefetch: bool,
    on_stage: Callable[[int, str, GraphState], None] | None,
    jobs: JobsPort | None = None,
) -> Callable[[GraphState], GraphState]:
    """Bind one workflow stage into a LangGraph node callable."""

    def node(state: GraphState) -> GraphState:
        output = _run_stage(
            tool,
            state,
            invoker,
            llm,
            retrieval=retrieval,
            prefetch=prefetch,
            catalogue=catalogue,
            expects_prefetch=expects_prefetch,
            jobs=jobs,
        )
        if on_stage is not None:
            merged: GraphState = {**state, **output}
            if is_prefetch_stage(tool, retrieval):
                slots = merged.get("slots") if isinstance(merged.get("slots"), dict) else {}
                emitted = False
                for key in slots:
                    key_s = str(key)
                    if key_s.startswith(f"{tool.get('id') or 'prefetch'}:"):
                        on_stage(index, key_s, merged)
                        emitted = True
                if not emitted:
                    on_stage(index, str(tool.get("id") or name), merged)
            else:
                on_stage(index, str(tool.get("id") or name), merged)
        return output
    return node


def build_tool_graph(
    tools: list[dict[str, Any]],
    invoker: ToolInvoker,
    llm: LlmPort | None = None,
    on_stage: Callable[[int, str, GraphState], None] | None = None,
    retrieval: dict[str, Any] | None = None,
    prefetch: PrefetchPort | None = None,
    catalogue: Any = None,
    *,
    start_index: int = 0,
    jobs: JobsPort | None = None,
):
    """Compile a LangGraph from hydrated tools; branch stages pick the next node from slots."""
    full_tools = tools
    if start_index:
        tools = tools[start_index:]
    expects_prefetch = _expects_prefetch_pack(tools)
    builder = StateGraph(GraphState)
    if not tools:

        def empty(state: GraphState) -> GraphState:
            """No tools: complete with an empty result."""
            return {"result": ""}

        builder.add_node("empty", empty)
        builder.add_edge(START, "empty")
        builder.add_edge("empty", END)
        return builder.compile()

    nodes: list[tuple[str, dict[str, Any], str]] = []
    for index, tool in enumerate(tools):
        name = _node_name(tool, index)
        stage_id = _stage_key(tool)
        bound = dict(tool)
        bound["_graph_index"] = start_index + index
        bound["_graph_tools"] = full_tools
        nodes.append((name, bound, stage_id))
        builder.add_node(
            name,
            _make_stage_node(
                name,
                bound,
                start_index + index,
                invoker,
                llm,
                retrieval=retrieval,
                prefetch=prefetch,
                catalogue=catalogue,
                expects_prefetch=expects_prefetch,
                on_stage=on_stage,
                jobs=jobs,
            ),
        )

    stage_to_node = {stage_id: node_name for node_name, _tool, stage_id in nodes if stage_id}
    branch_at = _branch_index(tools)
    if branch_at is None:
        previous = START
        for node_name, _tool, _stage_id in nodes:
            builder.add_edge(previous, node_name)
            previous = node_name
        builder.add_edge(previous, END)
        return builder.compile()

    branch_tool = nodes[branch_at][1]
    branch_map = branch_tool.get("branch")
    if not isinstance(branch_map, dict):
        raise RuntimeError("branch stage missing branch map")
    slot_key = branch_slot_key(branch_tool)
    branch_targets = {str(value) for value in branch_map.values()}
    merge_at = None
    for index in range(branch_at + 1, len(nodes)):
        if nodes[index][2] not in branch_targets:
            merge_at = index
            break
    if merge_at is None:
        raise RuntimeError("branch workflow missing merge stage after branch targets")

    previous = START
    for index in range(branch_at):
        builder.add_edge(previous, nodes[index][0])
        previous = nodes[index][0]
    builder.add_edge(previous, nodes[branch_at][0])

    branch_node_name = nodes[branch_at][0]
    route_map = {
        stage_to_node[target]: stage_to_node[target]
        for target in branch_targets
        if target in stage_to_node
    }
    if len(route_map) != len(branch_targets):
        missing = sorted(branch_targets - set(route_map))
        raise RuntimeError(f"branch targets missing from graph: {missing}")

    def route_branch(state: GraphState) -> str:
        slot_body = _slots(state).get(slot_key) or {}
        if not isinstance(slot_body, dict):
            slot_body = {}
        target_stage = resolve_branch_target(branch_map, slot_body)
        return stage_to_node[target_stage]

    builder.add_conditional_edges(branch_node_name, route_branch, route_map)

    merge_node_name = nodes[merge_at][0]
    for target in branch_targets:
        builder.add_edge(stage_to_node[target], merge_node_name)

    previous = merge_node_name
    for index in range(merge_at + 1, len(nodes)):
        builder.add_edge(previous, nodes[index][0])
        previous = nodes[index][0]
    builder.add_edge(previous, END)
    return builder.compile()


_LOOP_SYSTEM = (
    "You are an agent with domain tools. Reply with exactly one of:\n"
    "CALL <tool_id>\n"
    "ASK <question>\n"
    "DONE <answer>\n"
    "CALL may include a JSON object of input_schema fields on the next line "
    "(or after the tool id). Never send the customer utterance to a tool. "
    "ASK when a required locator (order id, customer id, or email) is missing. "
    "If prior stage outputs include a note starting with `customer:`, the customer "
    "just provided a locator — infer whether it is an order id (ORD-*), customer id "
    "(CUS-*), or email, then CALL the matching lookup tool with JSON args; do not ASK again. "
    "CALL a tool before DONE when tools can answer the goal. "
    "Do not invent tool results. After a tool output, CALL another tool or DONE. "
    "When DONE after a tool result, use that tool output as the answer unless the goal needs another tool. "
    "After escalate_to_human succeeds, you MUST DONE with a customer-facing summary that includes the handoff id. "
    "Never CALL escalate_to_human more than once."
)

_ESCALATE_TOOL_ID = "escalate_to_human"
_ASK_DEFAULT = (
    "Please provide an order id, customer id, or email so I can look up your order."
)


def _parse_json_object(raw: str) -> dict[str, Any] | None:
    """Return a dict if raw is a JSON object, else None."""
    text = (raw or "").strip()
    if not text.startswith("{"):
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_agent_line(text: str) -> tuple[str, str, dict[str, Any]]:
    """Parse CALL / ASK / DONE. CALL may carry a JSON object of tool args."""
    blob = (text or "").strip()
    if not blob:
        return "done", "", {}
    lines = [line.strip() for line in blob.splitlines() if line.strip()]
    first = lines[0]
    head, _, rest = first.partition(" ")
    token = head.strip().upper()
    if token == "CALL":
        tool_id = rest.strip().split()[0] if rest.strip() else ""
        leftover = rest.strip()[len(tool_id) :].strip() if tool_id else ""
        args = _parse_json_object(leftover) or {}
        if not args and len(lines) > 1:
            args = _parse_json_object("\n".join(lines[1:])) or {}
        if not tool_id:
            raise RuntimeError("CALL missing tool id")
        return "call", tool_id, args
    if token == "ASK":
        return "ask", rest.strip(), {}
    if token == "DONE":
        return "done", rest.strip(), {}
    return "done", blob, {}


def _handoff_id_from_slots(slots: dict[str, Any]) -> str:
    """Return handoff_id from escalate_to_human slot when present."""
    slot = slots.get(_ESCALATE_TOOL_ID)
    if not isinstance(slot, dict):
        return ""
    return str(slot.get("handoff_id") or "").strip()


def _escalate_succeeded(slots: dict[str, Any]) -> bool:
    """True when escalate_to_human produced a handoff (async ticket opened)."""
    return bool(_handoff_id_from_slots(slots))


def _pending_agent_joins(slots: dict[str, Any]) -> bool:
    """True when a kind=agent child was started but has not joined terminal yet."""
    for key, slot in slots.items():
        if key == _ESCALATE_TOOL_ID or not isinstance(slot, dict):
            continue
        corr = str(slot.get("correlation_id") or "").strip()
        if not corr and not slot.get("route_id"):
            continue
        # Joined packet shape: status + result. Bare start / in-flight child is pending.
        status = str(slot.get("status") or "").strip().lower()
        if status in {"completed", "failed"} and "result" in slot:
            continue
        if corr or slot.get("route_id"):
            return True
    return False


def _escalation_complete_message(slots: dict[str, Any], result: str) -> str:
    """Customer-facing summary after a successful escalation handoff."""
    handoff = _handoff_id_from_slots(slots)
    if handoff:
        return (
            f"I've escalated your case for human review. Reference {handoff}. "
            "Someone will follow up."
        )
    text = (result or "").strip()
    if text:
        return (
            f"I've escalated your case for human review. {text} "
            "Someone will follow up."
        )
    return "I've escalated your case for human review. Someone will follow up."


def _complete_after_escalate(
    current: GraphState,
    step: int,
    on_stage: Callable[[int, str, GraphState], None] | None,
) -> GraphState | None:
    """Auto-complete parent when escalate succeeded and no child join is still pending."""
    slots = _slots(current)
    if not _escalate_succeeded(slots):
        return None
    if _pending_agent_joins(slots):
        return None
    text = _escalation_complete_message(slots, str(current.get("result") or ""))
    out: GraphState = {
        **current,
        "result": text,
        "notes": list(current.get("notes") or []) + [text],
    }
    if on_stage is not None:
        on_stage(step, "respond", out)
    return out


def _idempotent_escalate_replay(
    current: GraphState,
    step: int,
    on_stage: Callable[[int, str, GraphState], None] | None,
) -> tuple[str, GraphState]:
    """Handle a repeated CALL escalate_to_human after a successful handoff.

    Returns (action, state):
    - ``complete`` — parent should finish now (no pending joins)
    - ``skip`` — do not POST again; keep looping (joins still pending)
    - ``call`` — no prior handoff; proceed with HTTP
    """
    slots = _slots(current)
    if not _escalate_succeeded(slots):
        return "call", current
    done = _complete_after_escalate(current, step, on_stage)
    if done is not None:
        return "complete", done
    handoff = _handoff_id_from_slots(slots)
    note = (
        f"escalate_to_human idempotent: handoff {handoff} already open; "
        "not creating another ticket"
    )
    skipped: GraphState = {
        **current,
        "result": str(current.get("result") or note),
        "notes": list(current.get("notes") or []) + [note],
    }
    if on_stage is not None:
        on_stage(step, _ESCALATE_TOOL_ID, skipped)
    return "skip", skipped


def build_agent_loop(
    tools: list[dict[str, Any]],
    invoker: ToolInvoker,
    llm: LlmPort,
    max_steps: int = 8,
    on_stage: Callable[[int, str, GraphState], None] | None = None,
    system: str = "",
    retrieval: dict[str, Any] | None = None,
    prefetch: PrefetchPort | None = None,
    catalogue: Any = None,
    jobs: JobsPort | None = None,
):
    """Pattern 1: LLM chooses CALL/DONE up to max_steps; CALL runs domain HTTP."""
    by_id = {str(tool.get("id") or ""): tool for tool in tools if tool.get("id")}
    catalog = ", ".join(sorted(by_id)) or "(none)"
    prompt = _LOOP_SYSTEM
    extra = (system or "").strip()
    if extra:
        prompt += f"\n{extra}"
    prompt += f"\nTools: {catalog}"

    class AgentLoop:
        def invoke(self, state: GraphState) -> GraphState:
            """Run the CALL/DONE loop and return the final graph state."""
            current: GraphState = {
                "result": str(state.get("result") or ""),
                "goal": dict(_mapping(state.get("goal"))),
                "notes": list(state.get("notes") or []),
                "slots": _slots(state),
                "correlation_id": str(state.get("correlation_id") or ""),
            }
            start_step = int(state.get("_resume_loop_step") or 0)
            for step in range(start_step, max(1, max_steps)):
                user = _user_blob(
                    _mapping(current.get("goal")),
                    list(current.get("notes") or []),
                    _slots(current),
                )
                raw = llm.complete(prompt, user)
                action, payload, call_args = _parse_agent_line(raw)
                if action == "ask":
                    text = payload or _ASK_DEFAULT
                    asked: GraphState = {
                        **current,
                        "result": text,
                        "notes": list(current.get("notes") or []) + [text],
                    }
                    telemetry.emit_stage_started("customer_ask", "none", user)
                    if on_stage is not None:
                        on_stage(step, "customer_ask", asked)
                    raise CustomerAskWaiting(
                        message=text,
                        step=step,
                        resume_loop_step=step + 1,
                        state=asked,
                    )
                if action == "done":
                    text = payload or str(current.get("result") or "")
                    current = {
                        **current,
                        "result": text,
                        "notes": list(current.get("notes") or []) + [text],
                    }
                    telemetry.emit_stage_started("respond", "synthesis", user)
                    if on_stage is not None:
                        on_stage(step, "respond", current)
                    return current
                pinned = dict(by_id.get(payload) or {})
                if not pinned:
                    raise RuntimeError(f"unknown tool {payload!r}")
                # Idempotent escalate: never POST a second handoff after success.
                if payload == _ESCALATE_TOOL_ID:
                    action_esc, current = _idempotent_escalate_replay(current, step, on_stage)
                    if action_esc == "complete":
                        return current
                    if action_esc == "skip":
                        continue
                http = dict(pinned)
                http["llm_role"] = "none"
                http["_graph_index"] = step
                try:
                    stage_out = _run_stage(
                        http,
                        current,
                        invoker,
                        llm,
                        retrieval=retrieval,
                        prefetch=prefetch,
                        catalogue=catalogue,
                        jobs=jobs,
                        call_args=call_args or None,
                    )
                except SubagentWaiting as exc:
                    raise SubagentWaiting(
                        stage_id=exc.stage_id,
                        gate_index=step,
                        resume_index=exc.resume_index,
                        subagent_ids=exc.subagent_ids,
                        state=exc.state,
                        resume_loop_step=step + 1,
                    ) from exc
                except RuntimeError as exc:
                    # Pattern 1: missing schema fields / tool HTTP → observe and continue (chat goal may only have utterance).
                    note = f"tool error ({payload}): {exc}"
                    telemetry.emit_stage_failed(payload, "none", call_args or current.get("goal") or {}, "runtime_error")
                    current = {
                        **current,
                        "result": note,
                        "notes": list(current.get("notes") or []) + [note],
                    }
                    if on_stage is not None:
                        on_stage(step, payload, current)
                    continue
                current = {**current, **stage_out}
                if on_stage is not None:
                    on_stage(step, payload, current)
                # First successful escalate + no pending joins → parent completes.
                if payload == _ESCALATE_TOOL_ID:
                    done = _complete_after_escalate(current, step, on_stage)
                    if done is not None:
                        return done
            raise RuntimeError(f"agent loop exceeded {max_steps} steps")

    return AgentLoop()
