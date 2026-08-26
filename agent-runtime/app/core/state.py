from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


def utcnow() -> datetime:
    """UTC timestamp used when writing run pins."""
    return datetime.now(timezone.utc)


@dataclass
class RunPin:
    correlation_id: str
    idempotency_key: str
    session_id: str
    route_id: str
    route_version: str
    activation_target: str | None
    agent_client_id: str | None
    hydrated_tools: list[dict[str, Any]]
    status: str
    result: dict[str, Any] | None = None
    checkpoint: dict[str, Any] | None = None
    working: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def slim_status(self) -> dict[str, Any]:
        """Channel-facing status: correlation id, status, and result if present."""
        body: dict[str, Any] = {
            "correlation_id": self.correlation_id,
            "status": self.status,
        }
        if self.result is not None:
            body["result"] = self.result
        return body

    def open_run(self) -> dict[str, Any]:
        """Session lookup payload: pin identity without hydrated tools."""
        return {
            "correlation_id": self.correlation_id,
            "session_id": self.session_id,
            "route_id": self.route_id,
            "route_version": self.route_version,
            "activation_target": self.activation_target,
            "agent_client_id": self.agent_client_id,
            "status": self.status,
        }


class RunStore(Protocol):
    def find_by_idempotency(self, key: str) -> RunPin | None: ...

    def get(self, correlation_id: str) -> RunPin | None: ...

    def find_by_session(self, session_id: str) -> RunPin | None: ...

    def insert(self, pin: RunPin) -> RunPin: ...

    def complete(self, correlation_id: str, result: dict[str, Any]) -> RunPin: ...

    def pause(
        self,
        correlation_id: str,
        *,
        working: dict[str, Any] | None = None,
        checkpoint: dict[str, Any] | None = None,
    ) -> RunPin: ...

    def fail(self, correlation_id: str, result: dict[str, Any]) -> RunPin: ...

    def mark_running(self, correlation_id: str) -> RunPin: ...

    def save_progress(
        self,
        correlation_id: str,
        *,
        working: dict[str, Any] | None = None,
        checkpoint: dict[str, Any] | None = None,
    ) -> None: ...

    def all(self) -> list[RunPin]: ...
