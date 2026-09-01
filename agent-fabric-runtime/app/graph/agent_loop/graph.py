from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.jobs_client import JobsPort
from app.agents.prefetch import PrefetchPort
from app.graph.agent_loop.completed_tool import replay_completed_tool, should_replay_completed_tool
from app.graph.agent_loop.decision import AgentDecision
from app.graph.agent_loop.handoff import (
    complete_after_handoff,
    handoff_from_slots,
    is_handoff_tool,
    replay_idempotent_handoff,
    subagent_joins_pending,
    try_complete_existing_handoff,
)
from app.graph.agent_loop.prompt import ASK_DEFAULT, build_agent_prompt
from app.graph.agent_loop.tools import index_tools
from app.graph.customer_ask import CustomerAskWaiting
from app.graph.llm.port import LlmPort
from app.graph.stage_runner import run_stage
from app.graph.payload import (
    grounding_ask_message,
    is_locator_preflight_error,
    validate_tool_payload,
)
from app.graph.state import (
    GraphState,
    append_unique_note,
    initial_loop_state,
    mapping,
    pending_customer_ask_message,
    slots,
    user_blob,
)
from app.graph.subagent_gate import SubagentWaiting
from app import telemetry
from app.tools.invoker import ToolInvoker


def _route_after_llm(state: GraphState) -> str:
    route = str(state.get("_route") or "end")
    if route == "tools":
        return "tools"
    return "end"


def build_agent_loop(
    tools: list[dict[str, Any]],
    invoker: ToolInvoker,
    llm: LlmPort,
    max_steps: int = 8,
    on_stage: Callable[[int, str, GraphState], None] | None = None,
    on_progress: Callable[[str], None] | None = None,
    system: str = "",
    retrieval: dict[str, Any] | None = None,
    prefetch: PrefetchPort | None = None,
    catalogue: Any = None,
    jobs: JobsPort | None = None,
):
    """Pattern 1: LangGraph loop where the LLM returns a structured AgentDecision.

    Nodes:
      llm   → decide (ask | done | tool_call)
      tools → execute selected capability, then back to llm
    """
    tool_index = index_tools(tools)
    prompt = build_agent_prompt(tools, system)

    def call_llm(state: GraphState) -> GraphState:
        return _decide(
            state,
            llm=llm,
            prompt=prompt,
            tool_index=tool_index,
            max_steps=max_steps,
            on_stage=on_stage,
            on_progress=on_progress,
        )

    def execute_tool(state: GraphState) -> GraphState:
        return _execute_tool(
            state,
            tool_index=tool_index,
            invoker=invoker,
            llm=llm,
            on_stage=on_stage,
            retrieval=retrieval,
            prefetch=prefetch,
            catalogue=catalogue,
            jobs=jobs,
        )

    graph = StateGraph(GraphState)
    graph.add_node("llm", call_llm)
    graph.add_node("tools", execute_tool)
    graph.add_edge(START, "llm")
    graph.add_conditional_edges(
        "llm",
        _route_after_llm,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "llm")
    return graph.compile()


def _emit_assistant_progress(
    on_progress: Callable[[str], None] | None,
    message: str | None,
) -> None:
    text = (message or "").strip()
    if text and on_progress is not None:
        on_progress(text)


def _decide(
    state: GraphState,
    *,
    llm: LlmPort,
    prompt: str,
    tool_index: dict[str, dict[str, Any]],
    max_steps: int,
    on_stage: Callable[[int, str, GraphState], None] | None,
    on_progress: Callable[[str], None] | None,
) -> GraphState:
    """Ask the LLM for the next AgentDecision and dispatch ask / done / tool_call."""
    current = initial_loop_state(state)
    step = int(current.get("step") or 0)
    if step >= max(1, max_steps):
        raise RuntimeError(f"agent loop exceeded {max_steps} steps")

    completed = try_complete_existing_handoff(current, step, on_stage)
    if completed is not None:
        return completed

    notes = list(current.get("notes") or [])
    user = user_blob(
        mapping(current.get("goal")),
        notes,
        slots(current),
    )
    pending_ask = pending_customer_ask_message(notes)
    if pending_ask:
        return _action_ask(
            current,
            step,
            AgentDecision(action="ask", message=pending_ask),
            user,
            on_stage,
        )
    decision = _complete_decision(llm, prompt, user)
    action = decision.action

    if action == "ask":
        return _action_ask(current, step, decision, user, on_stage)
    if action == "done":
        return _action_done(current, step, decision, user, on_stage)
    if action == "tool_call":
        routed = _action_tool_call(current, decision, tool_index)
        _emit_assistant_progress(on_progress, decision.message)
        preflight = routed.get("_preflight_error")
        if preflight and is_locator_preflight_error(str(preflight)):
            tool_id = (decision.tool_name or "").strip()
            pinned = dict(tool_index.get(tool_id) or {})
            input_schema = (
                pinned.get("input_schema") if isinstance(pinned.get("input_schema"), dict) else None
            )
            message = grounding_ask_message(tool_id, input_schema)
            return _action_ask(
                current,
                step,
                AgentDecision(action="ask", message=message),
                user,
                on_stage,
            )
        return routed
    raise RuntimeError(f"unsupported agent action: {action!r}")


def _complete_decision(llm: LlmPort, prompt: str, user: str) -> AgentDecision:
    token = telemetry.bind_llm_call_context(stage_id="agent_decision", llm_role="agent")
    try:
        return llm.complete_structured(system=prompt, user=user, schema=AgentDecision)
    finally:
        telemetry.reset_llm_call_context(token)


def _action_ask(
    current: GraphState,
    step: int,
    decision: AgentDecision,
    user: str,
    on_stage: Callable[[int, str, GraphState], None] | None,
) -> GraphState:
    text = decision.message or ASK_DEFAULT
    note = f"ask: {text}"
    prior_notes = list(current.get("notes") or [])
    new_notes = append_unique_note(prior_notes, note)
    re_ask = len(new_notes) == len(prior_notes)
    asked: GraphState = {
        **current,
        "result": text,
        "notes": new_notes,
        "_audit_request": user,
    }
    if not re_ask:
        telemetry.emit_stage_started("customer_ask", "none", user)
        if on_stage is not None:
            on_stage(step, "customer_ask", asked)
    raise CustomerAskWaiting(
        message=text,
        step=step,
        resume_loop_step=step + 1,
        state=asked,
    )


def _action_done(
    current: GraphState,
    step: int,
    decision: AgentDecision,
    user: str,
    on_stage: Callable[[int, str, GraphState], None] | None,
) -> GraphState:
    text = decision.message or str(current.get("result") or "")
    finished: GraphState = {
        **current,
        "result": text,
        "notes": append_unique_note(list(current.get("notes") or []), text),
        "_route": "end",
    }
    telemetry.emit_stage_started("respond", "synthesis", user)
    if on_stage is not None:
        on_stage(step, "respond", finished)
    return finished


def _action_tool_call(
    current: GraphState,
    decision: AgentDecision,
    tool_index: dict[str, dict[str, Any]],
) -> GraphState:
    tool_id = (decision.tool_name or "").strip()
    if not tool_id:
        raise RuntimeError("tool_call requires tool_name")
    if tool_id not in tool_index:
        raise RuntimeError(f"unknown or unauthorized tool {tool_id!r}")
    pinned = dict(tool_index[tool_id])
    input_schema = pinned.get("input_schema") if isinstance(pinned.get("input_schema"), dict) else None
    call_args = dict(decision.arguments or {})
    goal = mapping(current.get("goal"))
    slot_map = slots(current)
    notes = list(current.get("notes") or [])
    try:
        validate_tool_payload(goal, slot_map, input_schema, call_args, notes=notes)
    except RuntimeError as exc:
        return {
            **current,
            "_route": "tools",
            "_tool_id": tool_id,
            "_call_args": call_args,
            "_preflight_error": str(exc),
        }
    routed: GraphState = {
        **current,
        "_route": "tools",
        "_tool_id": tool_id,
        "_call_args": call_args,
    }
    text = (decision.message or "").strip()
    if text:
        routed["result"] = text
    return routed


def _execute_tool(
    state: GraphState,
    *,
    tool_index: dict[str, dict[str, Any]],
    invoker: ToolInvoker,
    llm: LlmPort,
    on_stage: Callable[[int, str, GraphState], None] | None,
    retrieval: dict[str, Any] | None,
    prefetch: PrefetchPort | None,
    catalogue: Any,
    jobs: JobsPort | None,
) -> GraphState:
    """Run the selected tool stage, then advance the loop step."""
    current = initial_loop_state(state)
    step = int(current.get("step") or 0)
    tool_id = str(state.get("_tool_id") or "")
    call_args = state.get("_call_args") if isinstance(state.get("_call_args"), dict) else {}
    pinned = dict(tool_index.get(tool_id) or {})
    if not pinned:
        raise RuntimeError(f"tool {tool_id!r} is not registered")

    preflight_error = state.get("_preflight_error")
    if preflight_error:
        return _tool_error(
            current,
            step,
            tool_id,
            call_args,
            RuntimeError(str(preflight_error)),
            on_stage,
        )

    if is_handoff_tool(pinned) and handoff_from_slots(slots(current)):
        return replay_idempotent_handoff(current, step, tool_id, on_stage)

    slot_map = slots(current)
    if should_replay_completed_tool(slot_map, tool_id, is_handoff=is_handoff_tool(pinned)):
        return replay_completed_tool(current, step, tool_id)

    http = dict(pinned)
    http["llm_role"] = "none"
    http["_graph_index"] = step

    try:
        stage_out = run_stage(
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
        return _tool_error(current, step, tool_id, call_args, exc, on_stage)

    merged: GraphState = {**current, **stage_out, "step": step + 1}
    if on_stage is not None:
        on_stage(step, tool_id, merged)
    if is_handoff_tool(pinned):
        found = handoff_from_slots(slots(merged))
        if found and not subagent_joins_pending(slots(merged)):
            stage_id, hid = found
            return complete_after_handoff(merged, step + 1, stage_id, hid, on_stage)
    return merged


def _tool_error(
    current: GraphState,
    step: int,
    tool_id: str,
    call_args: dict[str, Any] | None,
    exc: RuntimeError,
    on_stage: Callable[[int, str, GraphState], None] | None,
) -> GraphState:
    note = f"tool error ({tool_id}): {exc}"
    telemetry.emit_stage_failed(
        tool_id,
        "none",
        call_args or current.get("goal") or {},
        "runtime_error",
    )
    errored: GraphState = {
        **current,
        "result": note,
        "notes": append_unique_note(list(current.get("notes") or []), note),
        "step": step + 1,
    }
    if on_stage is not None:
        on_stage(step, tool_id, errored)
    return errored
