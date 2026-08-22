from typing import Any, Protocol

from app import telemetry
from app.core.state import RunPin, RunStore


class GraphPort(Protocol):
    def invoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


def run_loop(
    graph: GraphPort,
    store: RunStore,
    pin: RunPin,
    goal: dict[str, Any] | None = None,
    notes: list[str] | None = None,
) -> RunPin:
    """Invoke the graph for a pin and mark the run completed or failed."""
    if pin.session_id.startswith("job:"):
        journey_id = f"job.{pin.route_id}"
    elif pin.route_id:
        journey_id = f"chat.{pin.route_id}"
    else:
        journey_id = "chat.turn"
    try:
        with telemetry.tracer().start_as_current_span("graph.invoke") as span:
            span.set_attribute("correlation_id", pin.correlation_id)
            span.set_attribute("route_id", pin.route_id or "")
            span.set_attribute("session_id", pin.session_id)
            try:
                output = graph.invoke(
                    {"result": "", "goal": goal or {}, "notes": list(notes or [])}
                )
            except Exception as exc:
                telemetry.record_error(span, exc)
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
        telemetry.emit(
            "run.failed",
            journey_id=journey_id,
            correlation_id=pin.correlation_id,
            session_id=pin.session_id,
            route_id=pin.route_id,
            outcome="failed",
        )
        raise
