from typing import Any, Protocol

from app.store import RunPin, RunStore


class GraphPort(Protocol):
    def invoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


def run_stub_loop(graph: GraphPort, store: RunStore, pin: RunPin) -> RunPin:
    output = graph.invoke({"result": ""})
    message = str(output.get("result") or "")
    return store.complete(pin.correlation_id, {"message": message})
