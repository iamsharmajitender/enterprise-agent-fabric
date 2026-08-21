import uuid
from typing import Any

from app.hydrate import CataloguePort, HydrateError, RegistryPort, hydrate
from app.loop import GraphPort, run_stub_loop
from app.store import RunPin, RunStore


class RunService:
    def __init__(
        self,
        store: RunStore,
        catalogue: CataloguePort,
        registry: RegistryPort,
        graph: GraphPort,
    ) -> None:
        self._store = store
        self._catalogue = catalogue
        self._registry = registry
        self._graph = graph

    def start(self, body: dict[str, Any]) -> str:
        if body.get("mode") != "new":
            raise ValueError("mode must be new")
        key = str(body.get("idempotency_key") or "").strip()
        session_id = str(body.get("session_id") or "").strip()
        if not key or not session_id:
            raise ValueError("idempotency_key and session_id are required")
        existing = self._store.find_by_idempotency(key)
        if existing is not None:
            return existing.correlation_id
        tools = hydrate(body, self._catalogue, self._registry)
        pin = RunPin(
            correlation_id=_mint_correlation_id(),
            idempotency_key=key,
            session_id=session_id,
            route_id=str(body.get("route_id") or ""),
            route_version=str(body.get("route_version") or ""),
            activation_target=str(body.get("activation_target") or "") or None,
            agent_client_id=str(body.get("agent_client_id") or "") or None,
            hydrated_tools=tools,
            status="running",
        )
        saved = self._store.insert(pin)
        if saved.correlation_id != pin.correlation_id:
            return saved.correlation_id
        run_stub_loop(self._graph, self._store, saved)
        return saved.correlation_id

    def resume(self, correlation_id: str, body: dict[str, Any]) -> dict[str, Any] | None:
        pin = self._store.get(correlation_id)
        if pin is None:
            return None
        run_stub_loop(self._graph, self._store, pin)
        return self.status(correlation_id)

    def status(self, correlation_id: str) -> dict[str, Any] | None:
        pin = self._store.get(correlation_id)
        return None if pin is None else pin.slim_status()

    def open_run(self, session_id: str) -> dict[str, Any]:
        pin = self._store.find_by_session(session_id)
        if pin is None:
            return {"runs": []}
        return pin.open_run()


def _mint_correlation_id() -> str:
    return "corr-" + uuid.uuid4().hex[:12]
