from typing import Any, Protocol

from app import telemetry
from app.core.memory import checkpoint_payload, save_loop, save_working, working_payload
from app.core.session_ids import is_jobs_session
from app.core.state import RunPin, RunStore
from app.graph.human_gate import HumanGateWaiting
from app.graph.subagent_gate import SubagentWaiting


class GraphPort(Protocol):
    def invoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


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
    working = (
        working_payload(
            list(waiting_state.get("notes") or []),
            waiting_state.get("slots") if isinstance(waiting_state.get("slots"), dict) else {},
        )
        if save_working(profile)
        else None
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
    paused = store.pause(
        pin.correlation_id,
        working=working,
        checkpoint=checkpoint,
    )
    telemetry.emit(
        "run.waiting",
        journey_id=journey_id,
        correlation_id=pin.correlation_id,
        session_id=pin.session_id,
        route_id=pin.route_id,
        route_version=pin.route_version,
        outcome="waiting",
    )
    return paused


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
    """Invoke the graph for a pin and mark the run completed, waiting, or failed."""
    if is_jobs_session(pin.session_id):
        journey_id = f"job.{pin.route_id}"
    elif pin.route_id:
        journey_id = f"chat.{pin.route_id}"
    else:
        journey_id = "chat.turn"
    invoke_state: dict[str, Any] = {
        "result": "",
        "goal": goal or {},
        "notes": list(notes or []),
        "slots": dict(slots or {}),
        "correlation_id": pin.correlation_id,
    }
    if resume_loop_step is not None:
        invoke_state["_resume_loop_step"] = resume_loop_step
    try:
        with telemetry.tracer().start_as_current_span("graph.invoke") as span:
            span.set_attribute("correlation_id", pin.correlation_id)
            span.set_attribute("route_id", pin.route_id or "")
            span.set_attribute("session_id", pin.session_id)
            try:
                output = graph.invoke(invoke_state)
            except HumanGateWaiting as exc:
                telemetry.record_error(span, exc)
                return _pause_waiting(
                    store,
                    pin,
                    journey_id=journey_id,
                    waiting_for="human_gate",
                    stage_id=exc.stage_id,
                    gate_index=exc.gate_index,
                    resume_index=exc.resume_index,
                    waiting_state=exc.state,
                    profile=profile or {},
                )
            except SubagentWaiting as exc:
                telemetry.record_error(span, exc)
                extra: dict[str, Any] = {"subagent_ids": list(exc.subagent_ids)}
                if exc.resume_loop_step is not None:
                    extra["resume_loop_step"] = exc.resume_loop_step
                return _pause_waiting(
                    store,
                    pin,
                    journey_id=journey_id,
                    waiting_for="subagent",
                    stage_id=exc.stage_id,
                    gate_index=exc.gate_index,
                    resume_index=exc.resume_index,
                    waiting_state=exc.state,
                    profile=profile or {},
                    extra_checkpoint=extra,
                )
            except Exception as exc:
                telemetry.record_error(span, exc)
                profile_dict = profile or {}
                if save_loop(profile_dict):
                    latest = store.get(pin.correlation_id)
                    checkpoint = latest.checkpoint if latest and isinstance(latest.checkpoint, dict) else {}
                    if checkpoint.get("step") is not None:
                        failed = store.fail(
                            pin.correlation_id,
                            {"message": str(exc), "recoverable": True},
                        )
                        telemetry.emit(
                            "run.failed",
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
                    "run.failed",
                    journey_id=journey_id,
                    correlation_id=pin.correlation_id,
                    session_id=pin.session_id,
                    route_id=pin.route_id,
                    route_version=pin.route_version,
                    outcome="failed",
                )
                raise
        message = str(output.get("result") or "")
        completed = store.complete(pin.correlation_id, {"message": message})
        telemetry.emit(
            "run.completed",
            journey_id=journey_id,
            correlation_id=pin.correlation_id,
            session_id=pin.session_id,
            route_id=pin.route_id,
            route_version=pin.route_version,
            outcome="completed",
        )
        return completed
    except Exception:
        if not save_loop(profile or {}):
            telemetry.emit(
                "run.failed",
                journey_id=journey_id,
                correlation_id=pin.correlation_id,
                session_id=pin.session_id,
                route_id=pin.route_id,
                outcome="failed",
            )
        raise
