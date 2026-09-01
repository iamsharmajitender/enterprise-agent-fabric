from app.graph.payload import (
    merge_http_payload,
    parse_llm_slot,
    project_child_goal,
    project_slot,
    stage_note_from_response,
    validate_input_schema,
    validate_tool_payload,
)


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


def test_stage_note_from_response_uses_x_agent_context_fields() -> None:
    schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "policy_id": {"type": "string", "x-agent-context": True},
            "eligible": {"type": "boolean", "x-agent-context": True},
            "automatic_refund_limit": {"type": "number"},
            "recommended_action": {"type": "string", "x-agent-context": True},
        },
    }
    body = {
        "policy_id": "returns-v7",
        "eligible": True,
        "automatic_refund_limit": 75.0,
        "recommended_action": "escalate_to_human",
        "text": "Policy returns-v7: eligible for refund.",
    }
    note = stage_note_from_response(body, schema, stage_id="check_return_policy")
    assert note == (
        "check_return_policy: policy_id=returns-v7, eligible=true, "
        "recommended_action=escalate_to_human"
    )


def test_stage_note_from_response_falls_back_to_text_without_agent_context() -> None:
    schema = {
        "type": "object",
        "properties": {"text": {"type": "string"}, "order_id": {"type": "string"}},
    }
    body = {"text": "Order ORD-1 ready.", "order_id": "ORD-1"}
    assert stage_note_from_response(body, schema) == "Order ORD-1 ready."


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


def test_validate_input_schema_rejects_pattern_mismatch() -> None:
    schema = {
        "type": "object",
        "required": ["order_id"],
        "properties": {"order_id": {"type": "string", "pattern": "^ORD-\\d+$"}},
    }
    try:
        validate_input_schema({"order_id": "BAD-1"}, schema)
    except RuntimeError as exc:
        assert "validation failed" in str(exc)
        return
    raise AssertionError("expected pattern validation failure")


def test_validate_input_schema_accepts_matching_pattern() -> None:
    schema = {
        "type": "object",
        "required": ["order_id"],
        "properties": {"order_id": {"type": "string", "pattern": "^ORD-\\d+$"}},
    }
    validate_input_schema({"order_id": "ORD-77819"}, schema)


def test_validate_grounding_rejects_hallucinated_order_id() -> None:
    schema = {
        "type": "object",
        "required": ["order_id"],
        "properties": {
            "order_id": {
                "type": "string",
                "pattern": "^ORD-\\d+$",
                "x-ground-in-user-context": True,
            }
        },
    }
    goal = {"utterance": "My jacket arrived damaged"}
    try:
        validate_input_schema(
            {"order_id": "ORD-99999"},
            schema,
            goal=goal,
            notes=[],
            slots={},
        )
    except RuntimeError as exc:
        assert "not grounded" in str(exc)
        return
    raise AssertionError("expected grounding failure")


def test_validate_grounding_accepts_order_id_from_customer_note() -> None:
    schema = {
        "type": "object",
        "required": ["order_id"],
        "properties": {
            "order_id": {
                "type": "string",
                "pattern": "^ORD-\\d+$",
                "x-ground-in-user-context": True,
            }
        },
    }
    validate_input_schema(
        {"order_id": "ORD-77819"},
        schema,
        goal={"utterance": "help"},
        notes=["customer: ORD-77819"],
        slots={},
    )


def test_validate_grounding_skips_slot_sourced_order_id() -> None:
    schema = {
        "type": "object",
        "required": ["order_id"],
        "properties": {
            "order_id": {
                "type": "string",
                "pattern": "^ORD-\\d+$",
                "x-ground-in-user-context": True,
            }
        },
    }
    validate_input_schema(
        {"order_id": "ORD-77819"},
        schema,
        goal={"utterance": "check policy"},
        notes=[],
        slots={"lookup_order_by_order_id": {"order_id": "ORD-77819", "item_id": "jacket_blue_m"}},
    )


def test_validate_tool_payload_merges_and_validates() -> None:
    schema = {
        "type": "object",
        "required": ["order_id"],
        "properties": {
            "order_id": {
                "type": "string",
                "pattern": "^ORD-\\d+$",
                "x-ground-in-user-context": True,
            }
        },
    }
    payload = validate_tool_payload(
        {"utterance": "order ORD-22001 refund"},
        {},
        schema,
        {"order_id": "ORD-22001"},
        notes=[],
    )
    assert payload == {"order_id": "ORD-22001"}


def test_grounding_ask_message_for_lookup() -> None:
    from app.graph.payload import grounding_ask_message, is_grounding_preflight_error, is_locator_preflight_error

    assert is_grounding_preflight_error(
        "input_schema field 'order_id' value is not grounded in customer context"
    )
    assert is_locator_preflight_error("input_schema validation failed: pattern")
    assert not is_locator_preflight_error("input_schema missing required field 'order_id'")
    assert "ORD" in grounding_ask_message("lookup_order_by_order_id", None)


def test_validate_grounding_rejects_placeholder_order_id() -> None:
    schema = {
        "type": "object",
        "required": ["order_id"],
        "properties": {
            "order_id": {
                "type": "string",
                "pattern": "^ORD-\\d+$",
                "x-ground-in-user-context": True,
            }
        },
    }
    try:
        validate_input_schema(
            {"order_id": "ask"},
            schema,
            goal={"utterance": "jacket damaged"},
            notes=[],
            slots={},
        )
    except RuntimeError as exc:
        assert "not grounded" in str(exc)
        return
    raise AssertionError("expected placeholder grounding failure")
