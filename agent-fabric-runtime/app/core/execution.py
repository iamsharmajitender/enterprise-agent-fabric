"""Graph invoke wrapper: complete / pause / fail a RunPin.

run_loop sits between RunService (lifecycle) and LangGraph (stages).
Waiting exceptions (human_gate, customer_ask, subagent) are expected control
flow — they pause the pin rather than marking it failed.
"""

from typing import Any, Protocol

from app import telemetry
from app.core.memory import checkpoint_payload, save_loop, working_payload
from app.core.session_ids import is_jobs_session
from app.core.state import RunPin, RunStore
from app.graph.customer_ask import CustomerAskWaiting
from app.graph.human_gate import HumanGateWaiting
from app.graph.subagent_gate import SubagentWaiting


class GraphPort(Protocol):
    def invoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


def run_loop(
    graph: GraphPort,
    store: RunStore,
    pin: RunPin,
    goal: dict[str, Any] | None = None,
    notes: list[str] | None = None,
    slots: dict[str, Any] | None = None,
    *,
    profile: dict[str, Any] | None = None,
    resume_loop_step: int | None = None,
) -> RunPin:
    """Invoke the graph for a pin and mark the run completed, waiting, or failed.

    Thin orchestration:
    bind context → invoke → complete | pause | fail
    """
    journey_id = _journey_id(pin)
    invoke_state = _invoke_state(pin, goal, notes, slots, resume_loop_step)
    run_ctx_token = _bind_run_context(pin, journey_id)
    try:
        return _invoke_graph(graph, store, pin, invoke_state, journey_id, profile or {})
    except Exception:
        if not save_loop(profile or {}):
            telemetry.emit(
                "run.graph.failed",
                journey_id=journey_id,
                correlation_id=pin.correlation_id,
                session_id=pin.session_id,
                route_id=pin.route_id,
                outcome="failed",
            )
        raise
    finally:
        telemetry.reset_run_event_context(run_ctx_token)


def _journey_id(pin: RunPin) -> str:
    if is_jobs_session(pin.session_id):
        return f"job.{pin.route_id}"
    if pin.route_id:
        return f"chat.{pin.route_id}"
    return "chat.turn"


def _invoke_state(
    pin: RunPin,
    goal: dict[str, Any] | None,
    notes: list[str] | None,
    slots: dict[str, Any] | None,
    resume_loop_step: int | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "result": "",
        "goal": goal or {},
        "notes": list(notes or []),
        "slots": dict(slots or {}),
        "correlation_id": pin.correlation_id,
    }
    if resume_loop_step is not None:
        state["_resume_loop_step"] = resume_loop_step
    return state


def _bind_run_context(pin: RunPin, journey_id: str):
    ingress = "jobs" if is_jobs_session(pin.session_id) else "chat"
    return telemetry.bind_run_event_context(
        journey_id=journey_id,
        correlation_id=pin.correlation_id,
        session_id=pin.session_id,
        route_id=pin.route_id or "",
        route_version=pin.route_version or "",
        channel="web",
        ingress=ingress,
    )


def _invoke_graph(
    graph: GraphPort,
    store: RunStore,
    pin: RunPin,
    invoke_state: dict[str, Any],
    journey_id: str,
    profile: dict[str, Any],
) -> RunPin:
    with telemetry.tracer().start_as_current_span("graph.invoke") as span:
        span.set_attribute("correlation_id", pin.correlation_id)
        span.set_attribute("route_id", pin.route_id or "")
        span.set_attribute("session_id", pin.session_id)
        try:
            output = graph.invoke(invoke_state)
        except HumanGateWaiting as exc:
            return _handle_waiting(store, pin, span, journey_id, profile, exc, "human_gate")
        except CustomerAskWaiting as exc:
            return _handle_waiting(
                store,
                pin,
                span,
                journey_id,
                profile,
                exc,
                "customer_ask",
                extra_checkpoint={"resume_loop_step": exc.resume_loop_step},
            )
        except SubagentWaiting as exc:
            extra: dict[str, Any] = {"subagent_ids": list(exc.subagent_ids)}
            if exc.resume_loop_step is not None:
                extra["resume_loop_step"] = exc.resume_loop_step
            return _handle_waiting(
                store,
                pin,
                span,
                journey_id,
                profile,
                exc,
                "subagent",
                subagent_ids=exc.subagent_ids,
                extra_checkpoint=extra,
            )
        except Exception as exc:
            return _handle_failure(store, pin, span, journey_id, profile, exc)

        return _handle_completed(store, pin, journey_id, output)


def _handle_waiting(
    store: RunStore,
    pin: RunPin,
    span: Any,
    journey_id: str,
    profile: dict[str, Any],
    exc: HumanGateWaiting | CustomerAskWaiting | SubagentWaiting,
    waiting_for: str,
    *,
    subagent_ids: list[str] | None = None,
    extra_checkpoint: dict[str, Any] | None = None,
) -> RunPin:
    _mark_span_waiting(span, waiting_for, exc.stage_id, subagent_ids)
    return _pause_waiting(
        store,
        pin,
        journey_id=journey_id,
        waiting_for=waiting_for,
        stage_id=exc.stage_id,
        gate_index=exc.gate_index,
        resume_index=exc.resume_index,
        waiting_state=exc.state,
        profile=profile,
        extra_checkpoint=extra_checkpoint,
    )


def _handle_failure(
    store: RunStore,
    pin: RunPin,
    span: Any,
    journey_id: str,
    profile: dict[str, Any],
    exc: Exception,
) -> RunPin:
    telemetry.record_error(span, exc)
    if save_loop(profile):
        latest = store.get(pin.correlation_id)
        checkpoint = latest.checkpoint if latest and isinstance(latest.checkpoint, dict) else {}
        if checkpoint.get("step") is not None:
            failed = store.fail(
                pin.correlation_id,
                {"message": str(exc), "recoverable": True},
            )
            telemetry.emit(
                "run.graph.failed",
                journey_id=journey_id,
                correlation_id=pin.correlation_id,
                session_id=pin.session_id,
                route_id=pin.route_id,
                route_version=pin.route_version,
                outcome="failed_recoverable",
            )
            return failed
    store.fail(pin.correlation_id, {"message": str(exc)})
    telemetry.emit(
        "run.graph.failed",
        journey_id=journey_id,
        correlation_id=pin.correlation_id,
        session_id=pin.session_id,
        route_id=pin.route_id,
        route_version=pin.route_version,
        outcome="failed",
    )
    raise exc


def _handle_completed(
    store: RunStore,
    pin: RunPin,
    journey_id: str,
    output: dict[str, Any],
) -> RunPin:
    message = str(output.get("result") or "")
    completed = store.complete(pin.correlation_id, {"message": message})
    telemetry.emit(
        "run.graph.completed",
        journey_id=journey_id,
        correlation_id=pin.correlation_id,
        session_id=pin.session_id,
        route_id=pin.route_id,
        route_version=pin.route_version,
        outcome="completed",
    )
    return completed


def _mark_span_waiting(
    span: Any,
    waiting_for: str,
    stage_id: str,
    subagent_ids: list[str] | None = None,
) -> None:
    """Pause is expected control flow — keep the span OK and label why it stopped."""
    span.set_attribute("waiting_for", waiting_for)
    span.set_attribute("stage_id", stage_id)
    if subagent_ids:
        span.set_attribute("subagent_ids", ",".join(subagent_ids))


def _pause_waiting(
    store: RunStore,
    pin: RunPin,
    *,
    journey_id: str,
    waiting_for: str,
    stage_id: str,
    gate_index: int,
    resume_index: int,
    waiting_state: dict[str, Any],
    profile: dict[str, Any],
    extra_checkpoint: dict[str, Any] | None = None,
) -> RunPin:
    working = working_payload(
        list(waiting_state.get("notes") or []),
        waiting_state.get("slots") if isinstance(waiting_state.get("slots"), dict) else {},
    )
    checkpoint: dict[str, Any] = {
        "step": gate_index,
        "stage_id": stage_id,
        "resume_index": resume_index,
        "waiting_for": waiting_for,
        "goal": dict(waiting_state.get("goal") or {}),
    }
    if extra_checkpoint:
        checkpoint.update(extra_checkpoint)
    if save_loop(profile):
        checkpoint = {
            **checkpoint,
            **checkpoint_payload(
                gate_index,
                stage_id,
                str(waiting_state.get("result") or ""),
                dict(waiting_state.get("goal") or {}),
            ),
        }
        if extra_checkpoint:
            checkpoint.update(extra_checkpoint)
    ask_text = str(waiting_state.get("result") or "")
    paused = store.pause(
        pin.correlation_id,
        working=working,
        checkpoint=checkpoint,
        result={"message": ask_text} if ask_text else None,
    )
    telemetry.emit(
        "run.graph.waiting",
        journey_id=journey_id,
        correlation_id=pin.correlation_id,
        session_id=pin.session_id,
        route_id=pin.route_id,
        route_version=pin.route_version,
        outcome="waiting",
    )
    return paused
