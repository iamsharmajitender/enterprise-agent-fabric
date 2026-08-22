from typing import Any, Protocol

import httpx

from app import telemetry

_TIMEOUT = httpx.Timeout(5.0)


def _inject_request_id(request: httpx.Request) -> None:
    """Forward the edge request id on tool HTTP calls."""
    request_id = telemetry.current_request_id()
    if request_id:
        request.headers["X-Request-Id"] = request_id


class ToolInvoker(Protocol):
    def call(self, invoke: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]: ...


class HttpToolClient:
    def __init__(self) -> None:
        """HTTP client that calls a capability's invoke URL."""
        self._http = httpx.Client(timeout=_TIMEOUT, event_hooks={"request": [_inject_request_id]})

    def call(self, invoke: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        """POST (or configured method) JSON to invoke.url and return the body."""
        method = str(invoke.get("method") or "POST").upper()
        url = str(invoke.get("url") or "").strip()
        if not url:
            raise RuntimeError("tool invoke url missing")
        with telemetry.tracer().start_as_current_span("tool.invoke") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("tool.url", url.split("?", 1)[0])
            response = self._http.request(method, url, json=payload)
            span.set_attribute("http.status_code", response.status_code)
            try:
                response.raise_for_status()
            except Exception as exc:
                telemetry.record_error(span, exc)
                raise
            try:
                body = response.json()
            except ValueError:
                return {"text": response.text}
            if isinstance(body, dict):
                return body
            return {"text": str(body)}
