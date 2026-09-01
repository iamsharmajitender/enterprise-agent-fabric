import json
from typing import Any

from pydantic import ValidationError

from app.agents.prefetch import prefetch_pack_text
from app.graph.llm.schema import model_from_json_schema, usable_json_schema

X_AGENT_CONTEXT = "x-agent-context"
X_GROUND_IN_USER_CONTEXT = "x-ground-in-user-context"


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


def agent_context_field_names(output_schema: dict[str, Any] | None) -> list[str]:
    """Return output_schema property names marked with x-agent-context."""
    props = schema_properties(output_schema)
    return [
        name
        for name, spec in props.items()
        if isinstance(spec, dict) and spec.get(X_AGENT_CONTEXT) is True
    ]


def _format_agent_context_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:g}"
    if value is None:
        return "null"
    return str(value)


def stage_note_from_response(
    body: dict[str, Any],
    output_schema: dict[str, Any] | None,
    *,
    stage_id: str = "",
) -> str:
    """Build the LLM note for an HTTP stage from x-agent-context fields or text/message."""
    if not isinstance(body, dict):
        return str(body)
    fields = agent_context_field_names(output_schema)
    if fields:
        slot = project_slot(body, output_schema)
        parts = [
            f"{key}={_format_agent_context_value(slot[key])}"
            for key in fields
            if key in slot
        ]
        if parts:
            prefix = f"{stage_id}: " if stage_id else ""
            return prefix + ", ".join(parts)
    return str(body.get("text") or body.get("message") or "").strip()


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
    call_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project only input_schema keys from goal ∪ slots ∪ CALL args for a kind=agent child job."""
    merged = merge_http_payload(dict(goal), slots, input_schema, call_args)
    allowed = set(schema_properties(input_schema).keys())
    return {key: merged[key] for key in allowed if key in merged}


def merge_http_payload(
    goal: dict[str, Any],
    slots: dict[str, Any],
    input_schema: dict[str, Any] | None,
    call_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build domain HTTP JSON from goal, slots, and CALL args.

    When input_schema declares properties, only those keys are sent — never a
    raw chat utterance unless the schema lists it. CALL args win over goal.
    """
    payload = dict(goal)
    allowed = set(schema_properties(input_schema).keys())
    extra = call_args if isinstance(call_args, dict) else {}
    if not allowed:
        payload.update(extra)
        return payload
    for slot in slots.values():
        if not isinstance(slot, dict):
            continue
        for key, value in slot.items():
            if key in ("text", "notes"):
                continue
            if key in allowed and key not in payload:
                payload[key] = value
    for key, value in extra.items():
        if key in allowed:
            payload[key] = value
    if "packed_text" in allowed and "packed_text" not in payload:
        pack = prefetch_pack_text(slots)
        if pack:
            payload["packed_text"] = pack
    return {key: payload[key] for key in allowed if key in payload}


def user_context_text(goal: dict[str, Any], notes: list[str]) -> str:
    """Concatenate customer-facing goal fields and prior stage notes for grounding checks."""
    parts: list[str] = []
    utterance = goal.get("utterance")
    if utterance is not None:
        parts.append(str(utterance))
    for key, value in goal.items():
        if key == "utterance" or value is None:
            continue
        parts.append(str(value))
    parts.extend(str(note) for note in notes)
    return " ".join(parts)


def trusted_field_values(
    goal: dict[str, Any],
    slots: dict[str, Any],
    input_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    """Values already supplied by the channel goal or prior stage slots."""
    trusted: dict[str, Any] = {}
    for key in schema_properties(input_schema):
        if key in goal and goal[key] is not None:
            trusted[key] = goal[key]
        for slot in slots.values():
            if isinstance(slot, dict) and key in slot and slot[key] is not None:
                trusted[key] = slot[key]
    return trusted


def validate_grounded_fields(
    payload: dict[str, Any],
    input_schema: dict[str, Any] | None,
    *,
    goal: dict[str, Any],
    notes: list[str],
    slots: dict[str, Any],
) -> None:
    """Reject LLM-supplied identifiers that do not appear in customer context or prior slots."""
    if not input_schema:
        return
    props = schema_properties(input_schema)
    trusted = trusted_field_values(goal, slots, input_schema)
    context = user_context_text(goal, notes)
    for key, spec in props.items():
        if not isinstance(spec, dict) or not spec.get(X_GROUND_IN_USER_CONTEXT):
            continue
        if key not in payload or payload[key] is None:
            continue
        value = payload[key]
        if _is_placeholder_locator(value):
            raise RuntimeError(
                f"input_schema field {key!r} value is not grounded in customer context"
            )
        if key in trusted and trusted[key] == value:
            continue
        if str(value) not in context:
            raise RuntimeError(
                f"input_schema field {key!r} value is not grounded in customer context"
            )


GROUNDING_ERROR_FRAGMENT = "not grounded in customer context"
_LOCATOR_PREFLIGHT_MARKERS = (
    GROUNDING_ERROR_FRAGMENT,
    "input_schema validation failed",
)
_PLACEHOLDER_LOCATOR_VALUES = frozenset(
    {
        "ask",
        "stub",
        "unknown",
        "null",
        "none",
        "n/a",
        "na",
        "pending",
        "tbd",
        "missing",
        "placeholder",
        "?",
    }
)


def is_grounding_preflight_error(message: str) -> bool:
    """True when a tool_call was rejected because an identifier was not in customer context."""
    return is_locator_preflight_error(message)


def is_locator_preflight_error(message: str) -> bool:
    """True when a tool_call should pause for customer input instead of retrying."""
    text = message or ""
    return any(marker in text for marker in _LOCATOR_PREFLIGHT_MARKERS)


def _is_placeholder_locator(value: Any) -> bool:
    return str(value).strip().lower() in _PLACEHOLDER_LOCATOR_VALUES


def grounding_ask_message(tool_id: str, input_schema: dict[str, Any] | None) -> str:
    """Customer-facing prompt when the model tool_called with an ungrounded identifier."""
    if tool_id == "lookup_order_by_order_id":
        return "What is your order number? It should look like ORD-77819."
    grounded = [
        key
        for key, spec in schema_properties(input_schema).items()
        if isinstance(spec, dict) and spec.get(X_GROUND_IN_USER_CONTEXT)
    ]
    if grounded == ["order_id"]:
        return "What is your order number? It should look like ORD-77819."
    if grounded == ["customer_id"]:
        return "What is your customer id? It should look like CUS-12345."
    if grounded:
        labels = ", ".join(grounded)
        return f"Please provide {labels} from your account or order confirmation."
    return "Please provide the information needed to continue."


def validate_input_schema(
    payload: dict[str, Any],
    input_schema: dict[str, Any] | None,
    *,
    goal: dict[str, Any] | None = None,
    notes: list[str] | None = None,
    slots: dict[str, Any] | None = None,
) -> None:
    """Fail closed on missing required fields, JSON Schema constraints, and grounding rules."""
    if not input_schema:
        return
    for key in schema_required(input_schema):
        if key not in payload:
            raise RuntimeError(f"input_schema missing required field {key!r}")
        if payload[key] is None:
            raise RuntimeError(f"input_schema required field {key!r} is null")
    if goal is not None and notes is not None and slots is not None:
        validate_grounded_fields(payload, input_schema, goal=goal, notes=notes, slots=slots)
    bindable = usable_json_schema(input_schema)
    if bindable:
        try:
            model = model_from_json_schema(bindable, name="ToolInput")
            model.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError(f"input_schema validation failed: {exc}") from exc


def validate_tool_payload(
    goal: dict[str, Any],
    slots: dict[str, Any],
    input_schema: dict[str, Any] | None,
    call_args: dict[str, Any] | None,
    *,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    """Merge and validate a Pattern 1 tool_call before HTTP or subagent execution."""
    payload = merge_http_payload(goal, slots, input_schema, call_args)
    validate_input_schema(
        payload,
        input_schema,
        goal=goal,
        notes=notes or [],
        slots=slots,
    )
    return payload
