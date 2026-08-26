from typing import Any

import httpx

from app import telemetry
from app.agents.hydrate import HydrateError

_TIMEOUT = httpx.Timeout(5.0)
_HEADERS = {
    "Authorization": "Bearer fabric-internal",
    "X-Workload": "ar",
}


def _inject_request_id(request: httpx.Request) -> None:
    """Forward the edge request id on catalogue and registry calls."""
    request_id = telemetry.current_request_id()
    if request_id:
        request.headers["X-Request-Id"] = request_id


def _json_or_miss(response: httpx.Response, miss: str, error: str) -> dict[str, Any]:
    """Parse JSON, or raise HydrateError on 404 / 4xx-5xx."""
    if response.status_code == 404:
        raise HydrateError(miss)
    if response.status_code >= 400:
        raise HydrateError(error)
    return response.json()


def _optional_json(response: httpx.Response, label: str) -> dict[str, Any]:
    """Parse JSON, treating 404 as empty (workflow/prompt may be absent)."""
    if response.status_code == 404:
        return {}
    if response.status_code >= 400:
        raise HydrateError(f"{label} error {response.status_code}")
    body = response.json()
    return body if isinstance(body, dict) else {}


class HttpCatalogueClient:
    def __init__(self, base_url: str) -> None:
        """HTTP client for Data Plane catalogue reads."""
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=_TIMEOUT,
            headers=_HEADERS,
            event_hooks={"request": [_inject_request_id]},
        )

    def get_route(self, route_id: str, route_version: str) -> dict[str, Any]:
        """Fetch a pinned catalogue route row."""
        if not route_version:
            raise HydrateError("pinned version required")
        response = self._http.get(
            f"/v1/catalog/routes/{route_id}",
            params={"route_version": route_version},
        )
        return _json_or_miss(
            response,
            f"catalogue miss {route_id}@{route_version}",
            f"catalogue error {response.status_code}",
        )

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Fetch a workflow document, or {} if missing."""
        if not workflow_id:
            return {}
        return _optional_json(
            self._http.get(f"/v1/catalog/workflows/{workflow_id}"),
            "workflow",
        )

    def get_prompt(self, prompt_id: str) -> dict[str, Any]:
        """Fetch a prompt pack, or {} if missing."""
        if not prompt_id:
            return {}
        return _optional_json(
            self._http.get(f"/v1/catalog/prompts/{prompt_id}"),
            "prompt",
        )

    def get_corpus(self, corpus_id: str) -> dict[str, Any]:
        """Fetch a corpus row; fail closed when missing."""
        if not corpus_id:
            raise HydrateError("corpus id required")
        response = self._http.get(f"/v1/catalog/corpora/{corpus_id}")
        return _json_or_miss(
            response,
            f"corpus miss {corpus_id}",
            f"corpus error {response.status_code}",
        )


class HttpRegistryClient:
    def __init__(self, base_url: str) -> None:
        """HTTP client for Registry manifest and capability reads."""
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=_TIMEOUT,
            headers=_HEADERS,
            event_hooks={"request": [_inject_request_id]},
        )

    def get_manifest(self, manifest_id: str, manifest_version: str) -> dict[str, Any]:
        """Fetch a published tool manifest version."""
        response = self._http.get(f"/v1/manifests/{manifest_id}/versions/{manifest_version}")
        return _json_or_miss(
            response,
            f"manifest miss {manifest_id}@{manifest_version}",
            f"registry error {response.status_code}",
        )

    def get_capability(self, capability_id: str, version: str) -> dict[str, Any]:
        """Fetch a published capability (includes invoke URL)."""
        response = self._http.get(f"/v1/capabilities/{capability_id}/versions/{version}")
        return _json_or_miss(
            response,
            f"capability miss {capability_id}@{version}",
            f"registry error {response.status_code}",
        )
