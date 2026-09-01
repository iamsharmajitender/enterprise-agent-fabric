"""Build log/audit previews that mirror the messages sent to the LLM backend."""

from __future__ import annotations

from typing import Any

DEFAULT_SYSTEM = "Follow the user request. Reply with the result only."


def effective_system(system: str) -> str:
    """System prompt after the same default fallback ``ProviderLlm`` applies."""
    return system or DEFAULT_SYSTEM


def llm_messages_preview(
    system: str,
    user: str,
    *,
    structured: bool = False,
    schema_name: str | None = None,
    output_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full request preview: chat messages plus optional structured-output metadata."""
    preview: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": effective_system(system)},
            {"role": "user", "content": user},
        ],
    }
    if structured:
        preview["structured"] = True
        if schema_name:
            preview["schema_name"] = schema_name
        if output_schema:
            preview["output_schema"] = output_schema
    return preview
