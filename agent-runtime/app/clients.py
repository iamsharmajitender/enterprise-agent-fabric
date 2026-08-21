from typing import Any

import httpx

from app.hydrate import HydrateError

_TIMEOUT = httpx.Timeout(5.0)
_HEADERS = {
    "Authorization": "Bearer fabric-internal",
    "X-Workload": "ar",
}


class HttpCatalogueClient:
    def __init__(self, base_url: str) -> None:
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=_TIMEOUT, headers=_HEADERS)

    def get_route(self, route_id: str, route_version: str) -> dict[str, Any]:
        if not route_version:
            raise HydrateError("pinned version required")
        response = self._http.get(
            f"/v1/catalog/routes/{route_id}",
            params={"route_version": route_version},
        )
        if response.status_code == 404:
            raise HydrateError(f"catalogue miss {route_id}@{route_version}")
        if response.status_code >= 400:
            raise HydrateError(f"catalogue error {response.status_code}")
        return response.json()


class HttpRegistryClient:
    def __init__(self, base_url: str) -> None:
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=_TIMEOUT, headers=_HEADERS)

    def get_manifest(self, manifest_id: str, manifest_version: str) -> dict[str, Any]:
        response = self._http.get(f"/v1/manifests/{manifest_id}/versions/{manifest_version}")
        if response.status_code == 404:
            raise HydrateError(f"manifest miss {manifest_id}@{manifest_version}")
        if response.status_code >= 400:
            raise HydrateError(f"registry error {response.status_code}")
        return response.json()

    def get_capability(self, capability_id: str, version: str) -> dict[str, Any]:
        response = self._http.get(f"/v1/capabilities/{capability_id}/versions/{version}")
        if response.status_code == 404:
            raise HydrateError(f"capability miss {capability_id}@{version}")
        if response.status_code >= 400:
            raise HydrateError(f"registry error {response.status_code}")
        return response.json()
