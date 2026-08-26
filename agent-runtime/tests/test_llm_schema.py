from app.graph.llm.schema import (
    dump_structured,
    llm_output_schema,
    model_from_json_schema,
    stub_payload,
    usable_json_schema,
)

_RECEIPT = {
    "type": "object",
    "required": ["merchant", "amount", "date"],
    "properties": {
        "merchant": {"type": "string"},
        "amount": {"type": "number"},
        "currency": {"type": "string"},
        "date": {"type": "string"},
        "tax": {"type": "number"},
    },
}

_TEXT = {
    "type": "object",
    "required": ["text"],
    "properties": {"text": {"type": "string"}},
}


def test_usable_schema_keeps_receipt_fields() -> None:
    assert usable_json_schema(_RECEIPT) == _RECEIPT


def test_usable_schema_keeps_text_envelope() -> None:
    assert usable_json_schema(_TEXT) == _TEXT


def test_usable_schema_skips_empty_object() -> None:
    assert usable_json_schema({"type": "object"}) is None
    assert usable_json_schema({"type": "object", "properties": {}}) is None


def test_llm_output_schema_on_every_llm_role() -> None:
    pinned = {"output_schema": _RECEIPT}
    assert llm_output_schema(pinned, "classify") == _RECEIPT
    assert llm_output_schema(pinned, "synthesis") == _RECEIPT
    assert llm_output_schema(pinned, "query_formulation") == _RECEIPT
    assert llm_output_schema(pinned, "none") is None


def test_dump_structured_unwraps_text_envelope() -> None:
    assert dump_structured({"text": "Card frozen."}, _TEXT) == "Card frozen."
    assert '"merchant":"Acme"' in dump_structured(
        {"merchant": "Acme", "amount": 45.36, "date": "2026-08-12"}, _RECEIPT
    )


def test_pydantic_model_validates_required_fields() -> None:
    model = model_from_json_schema(_RECEIPT, name="extract_fields")
    parsed = model(merchant="Acme", amount=45.36, date="2026-08-12")
    assert parsed.merchant == "Acme"
    dumped = dump_structured(parsed, _RECEIPT)
    assert '"merchant":"Acme"' in dumped
    try:
        model(merchant="Acme")
    except Exception:
        return
    raise AssertionError("expected validation error")


def test_pydantic_model_keeps_description_and_constraints() -> None:
    schema = {
        "type": "object",
        "description": "Receipt fields from OCR notes.",
        "required": ["merchant", "date"],
        "properties": {
            "merchant": {
                "type": "string",
                "minLength": 1,
                "description": "Required; never null or empty.",
            },
            "date": {
                "type": "string",
                "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                "description": "Purchase date as YYYY-MM-DD.",
            },
        },
    }
    model = model_from_json_schema(schema, name="extract_fields")
    assert model.__doc__ == "Receipt fields from OCR notes."
    assert model.model_fields["merchant"].description == "Required; never null or empty."
    dumped = model.model_json_schema()
    assert dumped["properties"]["merchant"]["description"] == "Required; never null or empty."
    assert dumped["properties"]["merchant"]["minLength"] == 1
    assert dumped["properties"]["date"]["pattern"] == "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    parsed = model(merchant="Acme", date="2026-08-12")
    assert parsed.merchant == "Acme"
    try:
        model(merchant="", date="2026-08-12")
    except Exception:
        return
    raise AssertionError("expected empty merchant to fail")


def test_stub_payload_fills_required_only() -> None:
    assert stub_payload(_RECEIPT) == {
        "merchant": "stub",
        "amount": 0.0,
        "date": "stub",
    }


_INTAKE = {
    "type": "object",
    "description": "Return intake extraction. Always emit every required key.",
    "required": [
        "order_id",
        "reason",
        "missing_information",
        "confidence",
        "human_review_required",
        "human_review_reason",
    ],
    "properties": {
        "order_id": {
            "type": ["string", "null"],
            "description": "The order ID provided by the customer, or null if missing.",
        },
        "reason": {
            "type": "string",
            "enum": ["damaged_item", "wrong_item", "changed_mind", "unclear", "other"],
        },
        "missing_information": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Keys that are null or too unclear to extract.",
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence score from 0 to 1 for the extraction.",
        },
        "human_review_required": {"type": "boolean"},
        "human_review_reason": {"type": ["string", "null"]},
    },
}


def test_usable_schema_keeps_nullable_enum_and_array() -> None:
    assert usable_json_schema(_INTAKE) == _INTAKE
    assert usable_json_schema(
        {
            "type": "object",
            "properties": {"lines": {"type": "array", "items": {"type": "object"}}},
        }
    ) is None


def test_pydantic_model_binds_intake_extraction() -> None:
    model = model_from_json_schema(_INTAKE, name="return_intake")
    parsed = model(
        order_id=None,
        reason="damaged_item",
        missing_information=["order_id"],
        confidence=0.4,
        human_review_required=True,
        human_review_reason="order_id missing",
    )
    assert parsed.order_id is None
    dumped = model.model_json_schema()
    assert dumped["properties"]["reason"]["enum"] == [
        "damaged_item",
        "wrong_item",
        "changed_mind",
        "unclear",
        "other",
    ]
    assert dumped["properties"]["missing_information"]["items"]["type"] == "string"
    try:
        model(
            order_id=None,
            reason="not_a_reason",
            missing_information=[],
            confidence=0.4,
            human_review_required=False,
            human_review_reason=None,
        )
    except Exception:
        pass
    else:
        raise AssertionError("expected invalid enum to fail")
    try:
        model(
            reason="unclear",
            missing_information=[],
            confidence=0.4,
            human_review_required=False,
            human_review_reason=None,
        )
    except Exception:
        return
    raise AssertionError("expected missing required nullable order_id to fail")


def test_stub_payload_nullable_enum_and_array() -> None:
    assert stub_payload(_INTAKE) == {
        "order_id": None,
        "reason": "damaged_item",
        "missing_information": [],
        "confidence": 0.0,
        "human_review_required": False,
        "human_review_reason": None,
    }
