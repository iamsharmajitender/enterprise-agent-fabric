import json
import os
from typing import Any, Protocol

import httpx

from app import telemetry

_TIMEOUT = httpx.Timeout(10.0)


def _inject_request_id(request: httpx.Request) -> None:
    request_id = telemetry.current_request_id()
    if request_id:
        request.headers["X-Request-Id"] = request_id


def resolve_jobs_url(invoke_url: str) -> str:
    """Map catalogue agent invoke URLs to the configured API Front Door jobs endpoint."""
    afd = os.environ.get("AFD_URL", "http://localhost:3005").rstrip("/")
    raw = (invoke_url or "").strip()
    if not raw or "api-afd.internal" in raw or raw.endswith("/v1/jobs"):
        return f"{afd}/v1/jobs"
    return raw


class JobsPort(Protocol):
    def start(
        self,
        route_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
        *,
        invoke: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def status(self, correlation_id: str) -> dict[str, Any]: ...


class HttpJobsClient:
    """POST child jobs to API Front Door (calling-agent / stub channel auth in v1)."""

    def __init__(self) -> None:
        claims_raw = os.environ.get(
            "AFD_JOBS_CLAIMS",
            json.dumps({"sub": "agent-runtime", "emts": {}}, separators=(",", ":")),
        )
        self._claims_header = claims_raw
        self._http = httpx.Client(timeout=_TIMEOUT, event_hooks={"request": [_inject_request_id]})

    def start(
        self,
        route_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
        *,
        invoke: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = resolve_jobs_url(str((invoke or {}).get("url") or ""))
        body = {
            "route_id": route_id,
            "idempotency_key": idempotency_key,
            "payload": payload,
        }
        with telemetry.tracer().start_as_current_span("agent.start_job") as span:
            span.set_attribute("jobs.route_id", route_id)
            span.set_attribute("http.url", url.split("?", 1)[0])
            response = self._http.post(
                url,
                json=body,
                headers={
                    "Authorization": "Bearer stub",
                    "X-Stub-Claims": self._claims_header,
                    "Content-Type": "application/json",
                },
            )
            span.set_attribute("http.status_code", response.status_code)
            try:
                response.raise_for_status()
            except Exception as exc:
                telemetry.record_error(span, exc)
                raise
            result = response.json()
            if not isinstance(result, dict):
                raise RuntimeError("jobs start response must be a JSON object")
            return result

    def status(self, correlation_id: str) -> dict[str, Any]:
        afd = os.environ.get("AFD_URL", "http://localhost:3005").rstrip("/")
        url = f"{afd}/v1/jobs/{correlation_id}"
        with telemetry.tracer().start_as_current_span("agent.job_status") as span:
            span.set_attribute("jobs.correlation_id", correlation_id)
            span.set_attribute("http.url", url.split("?", 1)[0])
            response = self._http.get(
                url,
                headers={
                    "Authorization": "Bearer stub",
                    "X-Stub-Claims": self._claims_header,
                },
            )
            span.set_attribute("http.status_code", response.status_code)
            try:
                response.raise_for_status()
            except Exception as exc:
                telemetry.record_error(span, exc)
                raise
            result = response.json()
            if not isinstance(result, dict):
                raise RuntimeError("jobs status response must be a JSON object")
            return result
