from typing import Any

import httpx

from app import telemetry

_TIMEOUT = httpx.Timeout(5.0)


def _inject_request_id(request: httpx.Request) -> None:
    request_id = telemetry.current_request_id()
    if request_id:
        request.headers["X-Request-Id"] = request_id


class HttpPrefetchClient:
    def __init__(self) -> None:
        self._http = httpx.Client(timeout=_TIMEOUT, event_hooks={"request": [_inject_request_id]})

    def search(self, url: str, collection: str, goal: dict[str, Any]) -> list[dict[str, Any]]:
        """POST the catalogue corpus gateway and return chunk objects."""
        with telemetry.tracer().start_as_current_span("prefetch.search") as span:
            span.set_attribute("prefetch.collection", collection)
            span.set_attribute("http.url", url.split("?", 1)[0])
            response = self._http.post(
                url,
                json={"collection": collection, "goal": goal},
                headers={"Authorization": "Bearer fabric-internal", "X-Workload": "ar"},
            )
            span.set_attribute("http.status_code", response.status_code)
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise RuntimeError("prefetch response must be a JSON object")
            chunks = body.get("chunks")
            if not isinstance(chunks, list):
                raise RuntimeError("prefetch response missing chunks")
            return [chunk for chunk in chunks if isinstance(chunk, dict)]
