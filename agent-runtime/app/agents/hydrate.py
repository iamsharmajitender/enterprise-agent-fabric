from typing import Any, Protocol


class HydrateError(Exception):
    """Pinned catalogue or registry ref is missing; do not 202."""


class CataloguePort(Protocol):
    def get_route(self, route_id: str, route_version: str) -> dict[str, Any]: ...

    def get_workflow(self, workflow_id: str) -> dict[str, Any]: ...

    def get_prompt(self, prompt_id: str) -> dict[str, Any]: ...


class RegistryPort(Protocol):
    def get_manifest(self, manifest_id: str, manifest_version: str) -> dict[str, Any]: ...

    def get_capability(self, capability_id: str, version: str) -> dict[str, Any]: ...


def hydrate(
    start: dict[str, Any],
    catalogue: CataloguePort,
    registry: RegistryPort,
    row: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Resolve a pinned route into capability records plus llm_role / llm_prompt."""
    route_id = str(start.get("route_id") or "")
    route_version = str(start.get("route_version") or "")
    if not route_id or not route_version:
        raise HydrateError("pinned route_id and route_version are required")
    if row is None:
        row = catalogue.get_route(route_id, route_version)
    contract = start.get("contract") if isinstance(start.get("contract"), dict) else {}
    manifest_id = str(row.get("tool_manifest") or contract.get("tool_manifest") or "")
    manifest_version = str(
        row.get("tool_manifest_version") or contract.get("manifest_version") or ""
    )
    if manifest_id and manifest_version:
        hydrated = _hydrate_manifest(registry, manifest_id, manifest_version)
        _attach_llm_roles(catalogue, row, hydrated)
        return _ensure_llm(catalogue, row, hydrated)
    return _ensure_llm(catalogue, row, _hydrate_without_manifest(catalogue, row))


def _hydrate_manifest(
    registry: RegistryPort, manifest_id: str, manifest_version: str
) -> list[dict[str, Any]]:
    """Resolve published capability records from a pinned tool manifest."""
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


def _hydrate_without_manifest(catalogue: CataloguePort, row: dict[str, Any]) -> list[dict[str, Any]]:
    """Build graph nodes from a workflow or prompt pack when the route has no tools."""
    workflow_id = str(row.get("workflow_id") or "")
    prompt_id = str(row.get("prompt_id") or "")
    if workflow_id:
        return _hydrate_workflow(catalogue, row, workflow_id)
    if prompt_id:
        return _hydrate_prompt_only(catalogue, prompt_id)
    raise HydrateError("no manifest, workflow, or prompt on pinned catalogue row")


def _hydrate_workflow(
    catalogue: CataloguePort, row: dict[str, Any], workflow_id: str
) -> list[dict[str, Any]]:
    """One node per workflow stage; invoke stays empty so LLM-only stages skip HTTP."""
    workflow = catalogue.get_workflow(workflow_id)
    stages = workflow.get("stages") if isinstance(workflow.get("stages"), list) else []
    prompts, host = _prompt_pack(catalogue, str(row.get("prompt_id") or ""))
    hydrated: list[dict[str, Any]] = []
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            continue
        role = str(stage.get("llm_role") or "none")
        stage_id = str(stage.get("id") or stage.get("tool") or f"stage_{index}")
        hydrated.append(
            {
                "id": stage_id,
                "llm_role": role,
                "llm_prompt": prompts.get(role) or host,
                "invoke": {},
            }
        )
    if not hydrated:
        raise HydrateError("workflow has no stages")
    return hydrated


def _hydrate_prompt_only(catalogue: CataloguePort, prompt_id: str) -> list[dict[str, Any]]:
    """Pattern 0: a single synthesis node from the prompt pack host (or first role text)."""
    prompts, host = _prompt_pack(catalogue, prompt_id)
    text = host or next((body for body in prompts.values() if body), "")
    if not text:
        raise HydrateError("prompt pack empty on pinned catalogue row")
    return [{"id": prompt_id, "llm_role": "synthesis", "llm_prompt": text, "invoke": {}}]


def _roles_by_tool(catalogue: CataloguePort, workflow_id: str) -> dict[str, str]:
    """Read workflow stages into `{tool_id: llm_role}`."""
    if not workflow_id:
        return {}
    workflow = catalogue.get_workflow(workflow_id)
    stages = workflow.get("stages") if isinstance(workflow.get("stages"), list) else []
    roles: dict[str, str] = {}
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        tool_id = str(stage.get("tool") or "")
        if tool_id:
            roles[tool_id] = str(stage.get("llm_role") or "none")
    return roles


def _prompt_pack(catalogue: CataloguePort, prompt_id: str) -> tuple[dict[str, str], str]:
    """Read the prompt pack into `({llm_role: text}, host)`."""
    if not prompt_id:
        return {}, ""
    pack = catalogue.get_prompt(prompt_id)
    by_role = pack.get("by_llm_role") if isinstance(pack.get("by_llm_role"), dict) else {}
    prompts: dict[str, str] = {}
    for role, body in by_role.items():
        if isinstance(body, dict):
            prompts[str(role)] = str(body.get("text") or "")
    return prompts, str(pack.get("host") or "")


def _attach_llm_roles(
    catalogue: CataloguePort, row: dict[str, Any], tools: list[dict[str, Any]]
) -> None:
    """Stamp each hydrated capability with its workflow llm_role and prompt."""
    roles = _roles_by_tool(catalogue, str(row.get("workflow_id") or ""))
    prompts, _host = _prompt_pack(catalogue, str(row.get("prompt_id") or ""))
    for tool in tools:
        role = roles.get(str(tool.get("id") or ""), "none")
        tool["llm_role"] = role
        tool["llm_prompt"] = prompts.get(role, "")


_ANSWER_ROLES = frozenset({"classify", "synthesis"})
_DEFAULT_SYNTHESIS = (
    "Write the user-facing answer from the goal and prior stage outputs only. "
    "Do not invent facts that are not in those outputs."
)


def _has_answer(tools: list[dict[str, Any]]) -> bool:
    """True when a classify or synthesis node will write the user-facing answer."""
    return any(str(tool.get("llm_role") or "none") in _ANSWER_ROLES for tool in tools)


def _ensure_llm(
    catalogue: CataloguePort, row: dict[str, Any], tools: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Pattern 2/3 must not be HTTP-only. Pattern 1 is an LLM/tool loop at graph build."""
    mode = int(row.get("autonomy_mode") or 0)
    if mode in {0, 1} or _has_answer(tools):
        return tools
    prompts, host = _prompt_pack(catalogue, str(row.get("prompt_id") or ""))
    tools.append(
        {
            "id": "respond",
            "llm_role": "synthesis",
            "llm_prompt": prompts.get("synthesis") or host or _DEFAULT_SYNTHESIS,
            "invoke": {},
        }
    )
    return tools
