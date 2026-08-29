"""Async fire-and-forget audit emit to agent-audit-data-plane."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(3.0)
_HEADERS = {
    "Authorization": "Bearer fabric-internal",
    "X-Workload": "ar",
    "Accept": "application/json",
}


def _audit_url() -> str:
    return (os.environ.get("AUDIT_DATA_PLANE_URL") or "").strip()


def sha256_digest(raw: Any) -> str:
    text = raw if isinstance(raw, str) else json.dumps(raw, sort_keys=True, default=str)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def emit_async(event: dict[str, Any]) -> None:
    """Never raises; no-op when AUDIT_DATA_PLANE_URL unset."""
    base = _audit_url()
    if not base or not event:
        return

    def _send() -> None:
        try:
            with httpx.Client(base_url=base, timeout=_TIMEOUT, headers=_HEADERS) as client:
                client.post("/v1/audit/events", json=event)
        except Exception:
            log.warning("audit emit failed type=%s", event.get("event_type"), exc_info=True)

    threading.Thread(target=_send, name="ar-audit-emit", daemon=True).start()


def envelope(
    event_type: str,
    *,
    correlation_id: str | None,
    session_id: str | None,
    decision_id: str | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "occurred_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer": "ar",
        "correlation_id": correlation_id,
        "session_id": session_id,
        "decision_id": decision_id,
        "payload": payload,
    }


def hydrate_snapshot(
    correlation_id: str,
    session_id: str | None,
    route_id: str,
    route_version: str,
    tools: list[dict[str, Any]],
    manifest_id: str = "",
    manifest_version: str = "",
) -> dict[str, Any]:
    caps: list[dict[str, Any]] = []
    for tool in tools:
        invoke = tool.get("invoke") if isinstance(tool.get("invoke"), dict) else {}
        url = str(invoke.get("url") or "")
        caps.append(
            {
                "capability_id": str(tool.get("id") or ""),
                "capability_version": str(tool.get("version") or ""),
                "invoke_url_digest": sha256_digest(url) if url else None,
                "input_schema_digest": sha256_digest(tool.get("input_schema") or {}),
                "output_schema_digest": sha256_digest(tool.get("output_schema") or {}),
            }
        )
    return envelope(
        "hydrate.snapshot",
        correlation_id=correlation_id,
        session_id=session_id,
        decision_id=None,
        payload={
            "route_id": route_id,
            "route_version": route_version,
            "manifest_id": manifest_id or None,
            "manifest_version": manifest_version or None,
            "capabilities": caps,
        },
    )


def run_terminal(
    correlation_id: str,
    session_id: str | None,
    status: str,
    route_id: str,
    route_version: str,
    reason_code: str | None = None,
) -> dict[str, Any]:
    return envelope(
        "run.terminal",
        correlation_id=correlation_id,
        session_id=session_id,
        decision_id=None,
        payload={
            "status": status,
            "route_id": route_id,
            "route_version": route_version,
            "reason_code": reason_code,
        },
    )


def stage_completed(
    correlation_id: str,
    session_id: str | None,
    stage_id: str,
    llm_role: str,
    status: str,
    latency_ms: int,
    request_body: Any,
    response_body: Any,
) -> dict[str, Any]:
    return envelope(
        "stage.completed" if status == "completed" else "stage.failed",
        correlation_id=correlation_id,
        session_id=session_id,
        decision_id=None,
        payload={
            "stage_id": stage_id,
            "llm_role": llm_role,
            "status": status,
            "latency_ms": latency_ms,
            "request_digest": sha256_digest(request_body),
            "response_digest": sha256_digest(response_body),
        },
    )
