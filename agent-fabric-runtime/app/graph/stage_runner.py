"""Execute one hydrated capability node (shared by Patterns 0–3).

run_stage wraps telemetry; _run_stage_impl dispatches by kind:
  human_gate | llm-only | query_formulation | kind=agent | prefetch | HTTP tool
"""

from typing import Any

from app.agents.jobs_client import JobsPort
from app.agents.prefetch import (
    PrefetchPort,
    is_prefetch_stage,
    prefetch_corpus_stage_id,
    require_prefetch_pack,
    run_prefetch,
)
from app.graph.customer_ask import CustomerAskWaiting
from app.graph.human_gate import (
    HumanGateWaiting,
    gate_packet_present,
    human_gate_slot_key,
    resume_index_after_gate,
    waiting_message_for_gate,
)
from app.graph.llm import LlmPort
from app.graph.llm.messages import llm_messages_preview
from app.graph.llm.schema import llm_output_schema
from app.graph.payload import (
    merge_http_payload,
    parse_llm_slot,
    project_child_goal,
    project_slot,
    stage_note_from_response,
    validate_input_schema,
)
from app.graph.state import GraphState, append_unique_note, mapping, slots, user_blob
from app.graph.subagent_gate import (
    SubagentWaiting,
    join_enabled,
    subagent_result_present,
    subagent_result_text,
)
from app import telemetry
from app.tools.invoker import ToolInvoker

_LLM_ONLY_ROLES = frozenset({"classify", "synthesis"})
_KNOWN_LLM_ROLES = frozenset({"none", "query_formulation"}) | _LLM_ONLY_ROLES


def _stage_id(pinned: dict[str, Any]) -> str:
    return str(pinned.get("id") or "")


def _write_slot(
    slot_map: dict[str, Any],
    stage_id: str,
    body: dict[str, Any],
    pinned: dict[str, Any],
) -> dict[str, Any]:
    if not stage_id:
        return slot_map
    schema = pinned.get("output_schema") if isinstance(pinned.get("output_schema"), dict) else None
    updated = dict(slot_map)
    updated[stage_id] = project_slot(body, schema)
    return updated


def _llm_role(raw: Any) -> str:
    role = str(raw or "none").strip() or "none"
    if role not in _KNOWN_LLM_ROLES:
        raise RuntimeError(f"unknown llm_role {role!r}")
    return role


def _schema_label(schema: dict[str, Any] | None, *, pydantic_name: str | None = None) -> str | None:
    if pydantic_name:
        return pydantic_name
    if not schema:
        return None
    title = str(schema.get("title") or "").strip()
    return title or None


def _llm_messages_for_stage(
    pinned: dict[str, Any],
    goal: dict[str, Any],
    notes: list[str],
    slot_map: dict[str, Any],
    role: str,
    *,
    pydantic_schema_name: str | None = None,
) -> dict[str, Any]:
    system = str(pinned.get("llm_prompt") or "")
    user = user_blob(goal, notes, slot_map)
    output_schema = llm_output_schema(pinned, role)
    structured = output_schema is not None or pydantic_schema_name is not None
    schema_name = _schema_label(output_schema, pydantic_name=pydantic_schema_name)
    return llm_messages_preview(
        system,
        user,
        structured=structured,
        schema_name=schema_name,
        output_schema=output_schema,
    )


def _llm_complete(
    llm: LlmPort,
    prompt: str,
    user: str,
    pinned: dict[str, Any],
    role: str,
) -> str:
    stage_id = _stage_id(pinned)
    output_schema = llm_output_schema(pinned, role)
    token = telemetry.bind_llm_call_context(stage_id=stage_id, llm_role=role)
    try:
        if output_schema is not None:
            return llm.complete(prompt, user, schema=output_schema)
        return llm.complete(prompt, user)
    finally:
        telemetry.reset_llm_call_context(token)


def _stage_request_preview(
    pinned: dict[str, Any],
    goal: dict[str, Any],
    notes: list[str],
    slot_map: dict[str, Any],
    input_schema: dict[str, Any] | None,
    role: str,
    retrieval: dict[str, Any] | None,
    call_args: dict[str, Any] | None,
) -> Any:
    invoke = mapping(pinned.get("invoke"))
    if role in _LLM_ONLY_ROLES:
        return _llm_messages_for_stage(pinned, goal, notes, slot_map, role)
    payload = merge_http_payload(goal, slot_map, input_schema, call_args)
    if role == "query_formulation":
        llm_preview = _llm_messages_for_stage(pinned, goal, notes, slot_map, role)
        return {"tool_request": payload, "llm": llm_preview}
    if str(pinned.get("kind") or "") == "agent":
        return project_child_goal(goal, slot_map, input_schema, call_args)
    if is_prefetch_stage(pinned, retrieval):
        return goal
    if not str(invoke.get("url") or "").strip():
        return goal
    return payload


def run_stage(
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
    goal = mapping(state.get("goal"))
    notes = list(state.get("notes") or [])
    slot_map = slots(state)
    stage_id = _stage_id(pinned)
    role = _llm_role(pinned.get("llm_role"))
    input_schema = pinned.get("input_schema") if isinstance(pinned.get("input_schema"), dict) else None
    request_body = _stage_request_preview(
        pinned, goal, notes, slot_map, input_schema, role, retrieval, call_args
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
    """Execute one stage. Thin dispatcher over stage kinds."""
    invoke = mapping(pinned.get("invoke"))
    goal = mapping(state.get("goal"))
    notes = list(state.get("notes") or [])
    slot_map = slots(state)
    stage_id = _stage_id(pinned)
    role = _llm_role(pinned.get("llm_role"))
    prompt = str(pinned.get("llm_prompt") or "")
    input_schema = pinned.get("input_schema") if isinstance(pinned.get("input_schema"), dict) else None

    if str(pinned.get("stage_type") or "") == "human_gate":
        return _run_human_gate(pinned, state, goal, notes, slot_map)

    if role in _LLM_ONLY_ROLES:
        return _run_llm_only(
            pinned, llm, goal, notes, slot_map, stage_id, role, prompt,
            retrieval=retrieval, expects_prefetch=expects_prefetch,
        )

    payload = merge_http_payload(goal, slot_map, input_schema, call_args)
    if role == "query_formulation":
        payload = _apply_query_formulation(
            pinned, llm, goal, notes, slot_map, stage_id, prompt, payload,
            retrieval=retrieval, expects_prefetch=expects_prefetch,
        )

    if str(pinned.get("kind") or "") == "agent":
        return _run_subagent(
            pinned, state, jobs, invoke, goal, notes, slot_map, stage_id,
            input_schema, call_args,
        )

    url = str(invoke.get("url") or "")
    if not url:
        return _run_prefetch_or_passthrough(
            pinned, state, retrieval, prefetch, catalogue, goal, notes, slot_map, stage_id,
        )

    return _run_http_tool(
        pinned, invoker, invoke, payload, input_schema, notes, slot_map, stage_id, goal,
    )


def _run_human_gate(
    pinned: dict[str, Any],
    state: GraphState,
    goal: dict[str, Any],
    notes: list[str],
    slot_map: dict[str, Any],
) -> GraphState:
    gate_id = human_gate_slot_key(pinned)
    if gate_packet_present(slot_map, gate_id):
        return {"result": str(state.get("result") or ""), "notes": notes, "slots": slot_map}
    waiting_text = waiting_message_for_gate(pinned, dict(state))
    notes = append_unique_note(notes, waiting_text)
    raise HumanGateWaiting(
        stage_id=gate_id,
        gate_index=int(pinned.get("_graph_index") or 0),
        resume_index=resume_index_after_gate(
            pinned.get("_graph_tools") or [pinned],
            int(pinned.get("_graph_index") or 0),
        ),
        state={
            "result": waiting_text,
            "goal": goal,
            "notes": notes,
            "slots": slot_map,
        },
    )


def _run_llm_only(
    pinned: dict[str, Any],
    llm: LlmPort | None,
    goal: dict[str, Any],
    notes: list[str],
    slot_map: dict[str, Any],
    stage_id: str,
    role: str,
    prompt: str,
    *,
    retrieval: dict[str, Any] | None,
    expects_prefetch: bool,
) -> GraphState:
    if llm is None:
        raise RuntimeError(f"llm required for {role}")
    require_prefetch_pack(slot_map, retrieval, stage_id, expects_prefetch=expects_prefetch)
    user = user_blob(goal, notes, slot_map)
    text = _llm_complete(llm, prompt, user, pinned, role)
    notes.append(text)
    slot_body = parse_llm_slot(text)
    return {
        "result": text,
        "notes": notes,
        "slots": _write_slot(slot_map, stage_id, slot_body, pinned),
    }


def _apply_query_formulation(
    pinned: dict[str, Any],
    llm: LlmPort | None,
    goal: dict[str, Any],
    notes: list[str],
    slot_map: dict[str, Any],
    stage_id: str,
    prompt: str,
    payload: dict[str, Any],
    *,
    retrieval: dict[str, Any] | None,
    expects_prefetch: bool,
) -> dict[str, Any]:
    if llm is None:
        raise RuntimeError("llm required for query_formulation")
    require_prefetch_pack(slot_map, retrieval, stage_id, expects_prefetch=expects_prefetch)
    updated = dict(payload)
    updated["query"] = _llm_complete(
        llm, prompt, user_blob(goal, notes, slot_map), pinned, "query_formulation"
    )
    return updated


def _run_subagent(
    pinned: dict[str, Any],
    state: GraphState,
    jobs: JobsPort | None,
    invoke: dict[str, Any],
    goal: dict[str, Any],
    notes: list[str],
    slot_map: dict[str, Any],
    stage_id: str,
    input_schema: dict[str, Any] | None,
    call_args: dict[str, Any] | None,
) -> GraphState:
    if jobs is None:
        raise RuntimeError("jobs client required for kind=agent")
    if subagent_result_present(slot_map, stage_id):
        prior = slot_map.get(stage_id) if isinstance(slot_map.get(stage_id), dict) else {}
        prior = prior if isinstance(prior, dict) else {}
        text = subagent_result_text(
            prior.get("result"),
            status=str(prior.get("status") or "completed"),
            stage_id=stage_id,
        )
        if not text:
            text = str(state.get("result") or "")
        notes.append(text)
        return {"result": text, "notes": notes, "slots": slot_map}

    child_goal = project_child_goal(goal, slot_map, input_schema, call_args)
    validate_input_schema(child_goal, input_schema, goal=goal, notes=notes, slots=slot_map)
    invoke_body = invoke.get("body") if isinstance(invoke.get("body"), dict) else {}
    child_route_id = str(invoke_body.get("route_id") or "")
    if not child_route_id:
        raise RuntimeError("agent invoke missing route_id")
    parent_id = str(state.get("correlation_id") or "")
    idempotency_key = (
        f"subagent-{parent_id}-{stage_id}" if parent_id else f"subagent-{stage_id}"
    )
    started = jobs.start(child_route_id, idempotency_key, child_goal, invoke=invoke)
    child_correlation_id = str(started.get("correlation_id") or "")
    text = f"Started subagent {child_route_id} ({child_correlation_id})"
    notes.append(text)
    slot_body = {
        "route_id": child_route_id,
        "correlation_id": child_correlation_id,
        "payload": child_goal,
        "status": "running",
    }
    new_slots = _write_slot(slot_map, stage_id, slot_body, pinned)
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
    return {"result": text, "notes": notes, "slots": new_slots}


def _run_prefetch_or_passthrough(
    pinned: dict[str, Any],
    state: GraphState,
    retrieval: dict[str, Any] | None,
    prefetch: PrefetchPort | None,
    catalogue: Any,
    goal: dict[str, Any],
    notes: list[str],
    slot_map: dict[str, Any],
    stage_id: str,
) -> GraphState:
    if is_prefetch_stage(pinned, retrieval):
        if prefetch is None or catalogue is None:
            raise RuntimeError("prefetch client required")
        slot_body, note, per_corpus = run_prefetch(
            catalogue, prefetch, retrieval or {}, goal
        )
        notes.append(note)
        new_slots = _write_slot(slot_map, stage_id, slot_body, pinned)
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
        return {"result": note, "notes": notes, "slots": new_slots}
    result = notes[-1] if notes else str(state.get("result") or "")
    return {"result": result, "notes": notes, "slots": slot_map}


def _run_http_tool(
    pinned: dict[str, Any],
    invoker: ToolInvoker,
    invoke: dict[str, Any],
    payload: dict[str, Any],
    input_schema: dict[str, Any] | None,
    notes: list[str],
    slot_map: dict[str, Any],
    stage_id: str,
    goal: dict[str, Any],
) -> GraphState:
    validate_input_schema(payload, input_schema, goal=goal, notes=notes, slots=slot_map)
    response = invoker.call(invoke, payload)
    output_schema = pinned.get("output_schema") if isinstance(pinned.get("output_schema"), dict) else None
    text = stage_note_from_response(response, output_schema, stage_id=stage_id)
    notes = append_unique_note(notes, text)
    return {
        "result": text,
        "notes": notes,
        "slots": _write_slot(slot_map, stage_id, response, pinned),
    }
