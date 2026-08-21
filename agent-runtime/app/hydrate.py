from typing import Any, Protocol


class HydrateError(Exception):
    """Pinned catalogue or registry ref is missing; do not 202."""


class CataloguePort(Protocol):
    def get_route(self, route_id: str, route_version: str) -> dict[str, Any]: ...


class RegistryPort(Protocol):
    def get_manifest(self, manifest_id: str, manifest_version: str) -> dict[str, Any]: ...

    def get_capability(self, capability_id: str, version: str) -> dict[str, Any]: ...


def hydrate(start: dict[str, Any], catalogue: CataloguePort, registry: RegistryPort) -> list[dict[str, Any]]:
    route_id = str(start.get("route_id") or "")
    route_version = str(start.get("route_version") or "")
    if not route_id or not route_version:
        raise HydrateError("pinned route_id and route_version are required")
    row = catalogue.get_route(route_id, route_version)
    contract = start.get("contract") if isinstance(start.get("contract"), dict) else {}
    manifest_id = str(row.get("tool_manifest") or contract.get("tool_manifest") or "")
    manifest_version = str(
        row.get("tool_manifest_version") or contract.get("manifest_version") or ""
    )
    if not manifest_id or not manifest_version:
        raise HydrateError("manifest pointer missing on pinned catalogue row")
    manifest = registry.get_manifest(manifest_id, manifest_version)
    tools = manifest.get("tools") if isinstance(manifest.get("tools"), list) else []
    hydrated: list[dict[str, Any]] = []
    for tool in tools:
        if not isinstance(tool, dict):
            raise HydrateError("invalid tool ref")
        cap_id = str(tool.get("capability_id") or "")
        cap_version = str(tool.get("capability_version") or "")
        if not cap_id or not cap_version:
            raise HydrateError("tool ref missing capability pin")
        hydrated.append(registry.get_capability(cap_id, cap_version))
    return hydrated
