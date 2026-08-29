"""Turn a capability JSON Schema into a Pydantic model for structured LLM output."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, create_model

_PRIMITIVE = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
}
_TEXT_KEYS = frozenset({"text", "message"})
_LLM_ROLES = frozenset({"classify", "synthesis", "query_formulation"})


def llm_output_schema(pinned: dict[str, Any], role: str) -> dict[str, Any] | None:
    """Capability output_schema when this stage is an LLM call and the schema is bindable."""
    if role not in _LLM_ROLES:
        return None
    return usable_json_schema(pinned.get("output_schema"))


def usable_json_schema(raw: Any) -> dict[str, Any] | None:
    """Return a JSON Schema Runtime can bind, or None to stay free-form.

    Bindable: a flat object whose properties are primitives, primitive|null,
    enum, or arrays of primitives. Nested objects are not bindable.
    """
    if not isinstance(raw, dict):
        return None
    if raw.get("type") not in (None, "object"):
        return None
    props = raw.get("properties")
    if not isinstance(props, dict) or not props:
        return None
    for spec in props.values():
        if not isinstance(spec, dict) or not _bindable_property(spec):
            return None
    return raw


def model_from_json_schema(schema: dict[str, Any], *, name: str = "StageOutput") -> type[BaseModel]:
    """Build a Pydantic model so with_structured_output validates fields.

    ChatOllama.with_structured_output validates only when schema is a Pydantic
    class; a JSON Schema dict returns an unvalidated dict.
    Source: https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama/with_structured_output
    """
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required = {str(item) for item in (schema.get("required") or []) if item}
    fields: dict[str, Any] = {}
    for key, spec in props.items():
        if not isinstance(spec, dict):
            continue
        required_key = key in required
        annotation = _annotation(spec, omitable=not required_key)
        fields[str(key)] = (annotation, _field(spec, optional=not required_key))
    if not fields:
        raise ValueError("json schema has no bindable properties")
    docstring = str(schema.get("description") or "") or None
    return create_model(_model_name(name), __doc__=docstring, **fields)


def dump_structured(parsed: Any, schema: dict[str, Any] | None = None) -> str:
    """Serialize structured output. Unwrap {text}/{message} envelopes after validation."""
    if hasattr(parsed, "model_dump"):
        payload = parsed.model_dump(mode="json")
    elif isinstance(parsed, dict):
        payload = parsed
    else:
        payload = {"value": parsed}
    if isinstance(payload, dict) and _is_text_envelope(schema):
        for key in ("text", "message"):
            if payload.get(key) is not None:
                return str(payload[key])
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def stub_payload(schema: dict[str, Any]) -> dict[str, Any]:
    """Deterministic values matching required fields (seed stub, no model)."""
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required = {str(item) for item in (schema.get("required") or []) if item}
    body: dict[str, Any] = {}
    for key, spec in props.items():
        if key not in required:
            continue
        body[key] = _stub_value(spec if isinstance(spec, dict) else {})
    return body


def _bindable_property(spec: dict[str, Any]) -> bool:
    names = _type_names(spec.get("type"))
    allowed = set(_PRIMITIVE) | {"null", "array"}
    if not names or names - allowed:
        return False
    if "array" not in names:
        return True
    items = spec.get("items")
    if not isinstance(items, dict):
        return False
    item_names = _type_names(items.get("type"))
    return bool(item_names) and not (item_names - set(_PRIMITIVE) - {"null"})


def _annotation(spec: dict[str, Any], *, omitable: bool = False) -> Any:
    names = _type_names(spec.get("type"))
    nullable = "null" in names
    literals = _enum_literals(spec)
    if "array" in names:
        items = spec.get("items") if isinstance(spec.get("items"), dict) else {}
        inner = _annotation(items) if items else str
        base: Any = list[inner]
    elif literals:
        base = Literal[*literals]
    else:
        base = _python_type(names)
    if nullable or omitable:
        return base | None
    return base


def _enum_literals(spec: dict[str, Any]) -> tuple[Any, ...]:
    raw = spec.get("enum")
    if not isinstance(raw, list) or not raw:
        return ()
    values: list[Any] = []
    for item in raw:
        if item is None:
            continue
        if isinstance(item, bool):
            values.append(item)
        elif isinstance(item, (str, int, float)):
            values.append(item)
        else:
            return ()
    return tuple(values)


def _stub_value(spec: dict[str, Any]) -> Any:
    names = _type_names(spec.get("type"))
    if "null" in names:
        return None
    if "array" in names:
        return []
    literals = _enum_literals(spec)
    if literals:
        return literals[0]
    if "integer" in names:
        return 0
    if "number" in names:
        return 0.0
    if "boolean" in names:
        return False
    return "stub"


def _field(spec: dict[str, Any], *, optional: bool) -> Any:
    """Map JSON Schema description and constraints onto a Pydantic Field.

    description is sent to the model via with_structured_output. minLength /
    maxLength / minimum / maximum / pattern are validated after the completion.
    Field constraints: https://docs.pydantic.dev/latest/concepts/fields/#field-constraints
    JSON Schema metadata: https://docs.pydantic.dev/latest/concepts/fields/#customizing-json-schema
    """
    kwargs: dict[str, Any] = {}
    description = str(spec.get("description") or "")
    if description:
        kwargs["description"] = description
    min_length = spec.get("minLength")
    if isinstance(min_length, int):
        kwargs["min_length"] = min_length
    max_length = spec.get("maxLength")
    if isinstance(max_length, int):
        kwargs["max_length"] = max_length
    minimum = spec.get("minimum")
    if isinstance(minimum, (int, float)):
        kwargs["ge"] = minimum
    maximum = spec.get("maximum")
    if isinstance(maximum, (int, float)):
        kwargs["le"] = maximum
    pattern = spec.get("pattern")
    if isinstance(pattern, str) and pattern:
        kwargs["pattern"] = pattern
    if optional:
        return Field(default=None, **kwargs)
    return Field(..., **kwargs)


def _type_names(raw: Any) -> set[str]:
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {str(item) for item in raw if item}
    return set()


def _python_type(names: set[str]) -> type:
    for json_type, py_type in _PRIMITIVE.items():
        if json_type in names:
            return py_type
    return str


def _is_text_envelope(schema: dict[str, Any] | None) -> bool:
    if not isinstance(schema, dict):
        return False
    props = schema.get("properties")
    return isinstance(props, dict) and bool(props) and set(props) <= _TEXT_KEYS


def _model_name(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in raw)
    return (cleaned[:50] or "StageOutput").lstrip("0123456789") or "StageOutput"
