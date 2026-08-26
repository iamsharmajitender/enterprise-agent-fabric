import json
from typing import Any

from app.agents.prefetch import prefetch_pack_text


def schema_properties(schema: dict[str, Any] | None) -> dict[str, Any]:
    """Return input or output schema properties, or {}."""
    if not schema or not isinstance(schema.get("properties"), dict):
        return {}
    return schema["properties"]


def schema_required(schema: dict[str, Any] | None) -> list[str]:
    """Return required field names from a JSON Schema object."""
    if not schema:
        return []
    required = schema.get("required")
    return [str(key) for key in required] if isinstance(required, list) else []


def project_slot(body: dict[str, Any], output_schema: dict[str, Any] | None) -> dict[str, Any]:
    """Store only output_schema fields when properties are declared."""
    if not isinstance(body, dict):
        return {"text": str(body)}
    props = schema_properties(output_schema)
    if not props:
        return dict(body)
    keys = set(props.keys()) | set(schema_required(output_schema))
    return {key: body[key] for key in keys if key in body}


def parse_llm_slot(text: str) -> dict[str, Any]:
    """Parse classify/synthesis JSON into a slot object when possible."""
    stripped = (text or "").strip()
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {"text": text}


def project_child_goal(
    goal: dict[str, Any],
    slots: dict[str, Any],
    input_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    """Project only input_schema keys from goal ∪ slots for a kind=agent child job."""
    merged = merge_http_payload(dict(goal), slots, input_schema)
    allowed = set(schema_properties(input_schema).keys())
    return {key: merged[key] for key in allowed if key in merged}


def merge_http_payload(
    goal: dict[str, Any],
    slots: dict[str, Any],
    input_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build domain HTTP JSON from immutable goal plus prior slot keys the schema allows."""
    payload = dict(goal)
    allowed = set(schema_properties(input_schema).keys())
    if not allowed:
        return payload
    for slot in slots.values():
        if not isinstance(slot, dict):
            continue
        for key, value in slot.items():
            if key in ("text", "notes"):
                continue
            if key in allowed and key not in payload:
                payload[key] = value
    if "packed_text" in allowed and "packed_text" not in payload:
        pack = prefetch_pack_text(slots)
        if pack:
            payload["packed_text"] = pack
    return payload


def validate_input_schema(payload: dict[str, Any], input_schema: dict[str, Any] | None) -> None:
    """Fail closed when a required input_schema field is missing or null."""
    if not input_schema:
        return
    for key in schema_required(input_schema):
        if key not in payload:
            raise RuntimeError(f"input_schema missing required field {key!r}")
        if payload[key] is None:
            raise RuntimeError(f"input_schema required field {key!r} is null")
