from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, MetaData, Table, Text, Column, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.core.state import RunPin

metadata = MetaData(schema="runtime")

runs = Table(
    "runs",
    metadata,
    Column("correlation_id", Text, primary_key=True),
    Column("idempotency_key", Text, nullable=False, unique=True),
    Column("session_id", Text, nullable=False),
    Column("route_id", Text, nullable=False),
    Column("route_version", Text, nullable=False),
    Column("activation_target", Text),
    Column("agent_client_id", Text),
    Column("hydrated_tools", JSON, nullable=False),
    Column("status", Text, nullable=False),
    Column("result", JSON),
    Column("checkpoint", JSON),
    Column("working", JSON),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def _row_to_pin(row: Any) -> RunPin:
    """Map a runs table row onto a RunPin."""
    data = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
    return RunPin(
        correlation_id=data["correlation_id"],
        idempotency_key=data["idempotency_key"],
        session_id=data["session_id"],
        route_id=data["route_id"],
        route_version=data["route_version"],
        activation_target=data.get("activation_target"),
        agent_client_id=data.get("agent_client_id"),
        hydrated_tools=list(data.get("hydrated_tools") or []),
        status=data["status"],
        result=data.get("result"),
        checkpoint=data.get("checkpoint"),
        working=data.get("working"),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


class PersistentRunStore:
    def __init__(self, engine: Engine) -> None:
        """Bind this store to a database engine."""
        self._engine = engine

    def find_by_idempotency(self, key: str) -> RunPin | None:
        """Return the pin for an idempotency key, if one exists."""
        with self._engine.connect() as conn:
            row = conn.execute(select(runs).where(runs.c.idempotency_key == key)).first()
        return _row_to_pin(row) if row else None

    def get(self, correlation_id: str) -> RunPin | None:
        """Load one pin by correlation id."""
        with self._engine.connect() as conn:
            row = conn.execute(select(runs).where(runs.c.correlation_id == correlation_id)).first()
        return _row_to_pin(row) if row else None

    def find_by_session(self, session_id: str) -> RunPin | None:
        """Return the most recently updated pin for a session."""
        with self._engine.connect() as conn:
            row = conn.execute(
                select(runs)
                .where(runs.c.session_id == session_id)
                .order_by(runs.c.updated_at.desc())
                .limit(1)
            ).first()
        return _row_to_pin(row) if row else None

    def insert(self, pin: RunPin) -> RunPin:
        """Insert a pin; on idempotency conflict return the existing row."""
        values = {
            "correlation_id": pin.correlation_id,
            "idempotency_key": pin.idempotency_key,
            "session_id": pin.session_id,
            "route_id": pin.route_id,
            "route_version": pin.route_version,
            "activation_target": pin.activation_target,
            "agent_client_id": pin.agent_client_id,
            "hydrated_tools": pin.hydrated_tools,
            "status": pin.status,
            "result": pin.result,
            "checkpoint": pin.checkpoint,
            "working": pin.working,
            "created_at": pin.created_at,
            "updated_at": pin.updated_at,
        }
        try:
            with self._engine.begin() as conn:
                conn.execute(runs.insert().values(**values))
            return pin
        except IntegrityError:
            existing = self.find_by_idempotency(pin.idempotency_key)
            if existing is None:
                raise
            return existing

    def complete(self, correlation_id: str, result: dict[str, Any]) -> RunPin:
        """Mark the pin completed and persist the result payload."""
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            conn.execute(
                runs.update()
                .where(runs.c.correlation_id == correlation_id)
                .values(status="completed", result=result, updated_at=now)
            )
        pin = self.get(correlation_id)
        if pin is None:
            raise KeyError(correlation_id)
        return pin

    def pause(
        self,
        correlation_id: str,
        *,
        working: dict[str, Any] | None = None,
        checkpoint: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
    ) -> RunPin:
        """Mark the pin waiting and optionally persist a customer-facing result."""
        now = datetime.now(timezone.utc)
        values: dict[str, Any] = {"status": "waiting", "updated_at": now}
        if working is not None:
            values["working"] = working
        if checkpoint is not None:
            values["checkpoint"] = checkpoint
        if result is not None:
            values["result"] = result
        with self._engine.begin() as conn:
            conn.execute(
                runs.update().where(runs.c.correlation_id == correlation_id).values(**values)
            )
        pin = self.get(correlation_id)
        if pin is None:
            raise KeyError(correlation_id)
        return pin

    def fail(self, correlation_id: str, result: dict[str, Any]) -> RunPin:
        """Mark the pin failed and persist the result payload."""
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            conn.execute(
                runs.update()
                .where(runs.c.correlation_id == correlation_id)
                .values(status="failed", result=result, updated_at=now)
            )
        pin = self.get(correlation_id)
        if pin is None:
            raise KeyError(correlation_id)
        return pin

    def mark_running(self, correlation_id: str) -> RunPin:
        """Clear a terminal status so the graph can continue."""
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            conn.execute(
                runs.update()
                .where(runs.c.correlation_id == correlation_id)
                .values(status="running", result=None, updated_at=now)
            )
        pin = self.get(correlation_id)
        if pin is None:
            raise KeyError(correlation_id)
        return pin

    def save_progress(
        self,
        correlation_id: str,
        *,
        working: dict[str, Any] | None = None,
        checkpoint: dict[str, Any] | None = None,
    ) -> None:
        """Flush working notes and/or loop checkpoint while the run is in flight."""
        values: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
        if working is not None:
            values["working"] = working
        if checkpoint is not None:
            values["checkpoint"] = checkpoint
        if len(values) == 1:
            return
        with self._engine.begin() as conn:
            conn.execute(
                runs.update().where(runs.c.correlation_id == correlation_id).values(**values)
            )

    def all(self) -> list[RunPin]:
        """Return every pin (used by tests)."""
        with self._engine.connect() as conn:
            rows = conn.execute(select(runs)).all()
        return [_row_to_pin(row) for row in rows]
