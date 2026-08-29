from app.graph.payload import merge_http_payload, parse_llm_slot, project_child_goal, project_slot, validate_input_schema


def test_merge_http_payload_injects_packed_text_when_schema_allows() -> None:
    slots = {
        "prefetch": {
            "chunks": [{"corpus_id": "policy-engine", "id": "pe-1", "text": "Refund window is 30 days."}]
        }
    }
    schema = {
        "type": "object",
        "properties": {"topic": {"type": "string"}, "packed_text": {"type": "string"}},
    }
    payload = merge_http_payload({"topic": "refunds"}, slots, schema)
    assert "Refund window" in payload["packed_text"]
    assert payload["topic"] == "refunds"


def test_merge_http_payload_pulls_schema_keys_from_slots() -> None:
    goal = {"account_id": "a-1", "doc_id": "d-1"}
    slots = {
        "extract_fields": {"merchant": "Acme", "amount": 45.36, "date": "2026-08-12"},
        "ocr": {"text": "OCR prose must not merge"},
    }
    schema = {
        "type": "object",
        "required": ["account_id", "merchant", "amount", "date"],
        "properties": {
            "account_id": {"type": "string"},
            "merchant": {"type": "string"},
            "amount": {"type": "number"},
            "date": {"type": "string"},
        },
    }
    assert merge_http_payload(goal, slots, schema) == {
        "account_id": "a-1",
        "merchant": "Acme",
        "amount": 45.36,
        "date": "2026-08-12",
    }


def test_merge_http_payload_drops_utterance_when_schema_omits_it() -> None:
    schema = {
        "type": "object",
        "required": ["order_id"],
        "properties": {"order_id": {"type": "string"}},
    }
    payload = merge_http_payload(
        {"utterance": "jacket damaged", "order_id": "ORD-1"},
        {},
        schema,
    )
    assert payload == {"order_id": "ORD-1"}


def test_merge_http_payload_call_args_win_over_goal() -> None:
    schema = {
        "type": "object",
        "properties": {"order_id": {"type": "string"}, "email": {"type": "string"}},
    }
    payload = merge_http_payload(
        {"order_id": "ORD-OLD"},
        {},
        schema,
        {"order_id": "ORD-77819"},
    )
    assert payload == {"order_id": "ORD-77819"}


def test_project_slot_keeps_output_schema_subset() -> None:
    body = {"text": "ok", "card_id": "c-1", "secret": "drop-me"}
    schema = {
        "type": "object",
        "required": ["text"],
        "properties": {"text": {"type": "string"}, "card_id": {"type": "string"}},
    }
    assert project_slot(body, schema) == {"text": "ok", "card_id": "c-1"}


def test_parse_llm_slot_reads_json() -> None:
    assert parse_llm_slot('{"merchant":"Acme"}') == {"merchant": "Acme"}
    assert parse_llm_slot("plain text") == {"text": "plain text"}


def test_project_child_goal_keeps_only_schema_keys() -> None:
    schema = {
        "type": "object",
        "required": ["document_id"],
        "properties": {
            "document_id": {"type": "string"},
            "matter_id": {"type": "string"},
        },
    }
    goal = {"document_id": "doc-1", "noise": "drop-me"}
    slots = {"ocr_extract": {"matter_id": "m-9", "text": "ignore"}}
    assert project_child_goal(goal, slots, schema) == {
        "document_id": "doc-1",
        "matter_id": "m-9",
    }


def test_validate_input_schema_fails_closed() -> None:
    schema = {
        "type": "object",
        "required": ["merchant", "amount"],
        "properties": {"merchant": {"type": "string"}, "amount": {"type": "number"}},
    }
    try:
        validate_input_schema({"merchant": "Acme"}, schema)
    except RuntimeError as exc:
        assert "amount" in str(exc)
        return
    raise AssertionError("expected validation failure")
