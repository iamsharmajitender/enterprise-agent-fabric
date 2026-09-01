from typing import Any


def index_tools(tools: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map each hydrated capability id to its pinned tool record."""
    return {str(tool.get("id") or ""): tool for tool in tools if tool.get("id")}
