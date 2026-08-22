from app.core.state import RunPin, utcnow


class InMemoryRunStore:
    def __init__(self) -> None:
        self._by_id: dict[str, RunPin] = {}
        self._by_key: dict[str, str] = {}

    def find_by_idempotency(self, key: str) -> RunPin | None:
        correlation_id = self._by_key.get(key)
        return self._by_id.get(correlation_id) if correlation_id else None

    def get(self, correlation_id: str) -> RunPin | None:
        return self._by_id.get(correlation_id)

    def find_by_session(self, session_id: str) -> RunPin | None:
        matches = [pin for pin in self._by_id.values() if pin.session_id == session_id]
        if not matches:
            return None
        return max(matches, key=lambda pin: pin.updated_at)

    def insert(self, pin: RunPin) -> RunPin:
        existing = self.find_by_idempotency(pin.idempotency_key)
        if existing is not None:
            return existing
        self._by_id[pin.correlation_id] = pin
        self._by_key[pin.idempotency_key] = pin.correlation_id
        return pin

    def complete(self, correlation_id: str, result: dict) -> RunPin:
        pin = self._by_id[correlation_id]
        pin.status = "completed"
        pin.result = result
        pin.updated_at = utcnow()
        return pin

    def save_progress(
        self,
        correlation_id: str,
        *,
        working: dict | None = None,
        checkpoint: dict | None = None,
    ) -> None:
        pin = self._by_id[correlation_id]
        if working is not None:
            pin.working = working
        if checkpoint is not None:
            pin.checkpoint = checkpoint
        pin.updated_at = utcnow()

    def all(self) -> list[RunPin]:
        return list(self._by_id.values())
