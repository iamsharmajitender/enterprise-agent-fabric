from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.prefetch import (
    PREFETCH_SLOT_ID,
    PrefetchPort,
    is_prefetch_stage,
    prefetch_pack_text,
    require_prefetch_pack,
    run_prefetch,
)
from app.agents.jobs_client import JobsPort
from app.graph.branch import branch_slot_key, resolve_branch_target
from app.graph.human_gate import (
    HumanGateWaiting,
    gate_packet_present,
    human_gate_slot_key,
    resume_index_after_gate,
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
    return str(body.get("text") or body.get("message") or "")


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
) -> GraphState:
    """Run one hydrated capability: LLM-only, LLM-then-HTTP, HTTP, or no-op."""
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
    payload = merge_http_payload(goal, slots, input_schema)
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
        child_goal = project_child_goal(goal, slots, input_schema)
        validate_input_schema(child_goal, input_schema)
        invoke_body = invoke.get("body") if isinstance(invoke.get("body"), dict) else {}
        child_route_id = str(invoke_body.get("route_id") or "")
        if not child_route_id:
            raise RuntimeError("agent invoke missing route_id")
        parent_id = str(state.get("correlation_id") or "")
        idempotency_key = (
            f"child-{parent_id}-{stage_id}" if parent_id else f"child-{stage_id}"
        )
        started = jobs.start(
            child_route_id,
            idempotency_key,
            child_goal,
            invoke=invoke,
        )
        child_correlation_id = str(started.get("correlation_id") or "")
        text = f"Started child job {child_route_id} ({child_correlation_id})"
        notes.append(text)
        slot_body = {
            "route_id": child_route_id,
            "correlation_id": child_correlation_id,
            "payload": child_goal,
        }
        return {
            "result": text,
            "notes": notes,
            "slots": _write_slot(slots, stage_id, slot_body, pinned),
        }
    url = str(invoke.get("url") or "")
    if not url:
        if is_prefetch_stage(pinned, retrieval):
            if prefetch is None or catalogue is None:
                raise RuntimeError("prefetch client required")
            slot_body, note = run_prefetch(catalogue, prefetch, retrieval or {}, goal)
            notes.append(note)
            return {
                "result": note,
                "notes": notes,
                "slots": _write_slot(slots, stage_id, slot_body, pinned),
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
    "You are an agent with domain tools. Reply with exactly one line:\n"
    "CALL <tool_id>\n"
    "or\n"
    "DONE <answer>\n"
    "CALL a tool before DONE when tools can answer the goal. "
    "Do not invent tool results. After a tool output, CALL another tool or DONE. "
    "When DONE after a tool result, use that tool output as the answer unless the goal needs another tool."
)


def _parse_agent_line(text: str) -> tuple[str, str]:
    """Parse a CALL <id> or DONE <answer> line from the model."""
    line = (text or "").strip().splitlines()[0].strip() if text else ""
    head, _, rest = line.partition(" ")
    token = head.strip().upper()
    if token == "CALL":
        tool_id = rest.strip().split()[0] if rest.strip() else ""
        if not tool_id:
            raise RuntimeError("CALL missing tool id")
        return "call", tool_id
    if token == "DONE":
        return "done", rest.strip()
    return "done", (text or "").strip()


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
            }
            start_step = int(state.get("_resume_loop_step") or 0)
            for step in range(start_step, max(1, max_steps)):
                user = _user_blob(
                    _mapping(current.get("goal")),
                    list(current.get("notes") or []),
                    _slots(current),
                )
                raw = llm.complete(prompt, user)
                action, payload = _parse_agent_line(raw)
                if action == "done":
                    text = payload or str(current.get("result") or "")
                    current = {
                        **current,
                        "result": text,
                        "notes": list(current.get("notes") or []) + [text],
                    }
                    if on_stage is not None:
                        on_stage(step, "respond", current)
                    return current
                pinned = dict(by_id.get(payload) or {})
                if not pinned:
                    raise RuntimeError(f"unknown tool {payload!r}")
                http = dict(pinned)
                http["llm_role"] = "none"
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
                    )
                except RuntimeError as exc:
                    # Pattern 1: missing schema fields / tool HTTP → observe and continue (chat goal may only have utterance).
                    note = f"tool error ({payload}): {exc}"
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
            raise RuntimeError(f"agent loop exceeded {max_steps} steps")

    return AgentLoop()
