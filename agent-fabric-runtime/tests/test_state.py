from app.graph.state import (
    append_customer_reply,
    append_unique_note,
    compress_notes_for_llm,
    pending_customer_ask_message,
    user_blob,
)


def test_append_unique_note_skips_consecutive_duplicate() -> None:
    assert append_unique_note(["a"], "a") == ["a"]
    assert append_unique_note(["a"], "b") == ["a", "b"]


def test_compress_notes_for_llm_keeps_latest_stage_note() -> None:
    notes = [
        "customer: ORD-1",
        "lookup_order_by_order_id: order_id=ORD-1, item_id=jacket_blue_m",
        "lookup_order_by_order_id: order_id=ORD-1, item_id=jacket_blue_m",
        "lookup_order_by_order_id: already completed; use prior stage outputs",
    ]
    assert compress_notes_for_llm(notes) == [
        "customer: ORD-1",
        "lookup_order_by_order_id: already completed; use prior stage outputs",
    ]


def test_user_blob_uses_compressed_notes() -> None:
    blob = user_blob(
        {"utterance": "help"},
        [
            "lookup_order_by_order_id: order_id=ORD-1",
            "lookup_order_by_order_id: order_id=ORD-1",
            "lookup_order_by_order_id: already completed",
        ],
    )
    assert blob.count("lookup_order_by_order_id:") == 1
    assert "already completed" in blob


def test_pending_customer_ask_message() -> None:
    assert pending_customer_ask_message([]) is None
    ask = "What is your order number? It should look like ORD-77819."
    assert pending_customer_ask_message([f"ask: {ask}"]) == ask
    assert pending_customer_ask_message([f"ask: {ask}", "customer: ORD-77819"]) is None
    assert pending_customer_ask_message([f"ask: {ask}", "tool error (lookup): boom", f"ask: {ask}"]) == ask


def test_append_customer_reply_appends_once_per_ask() -> None:
    ask = "What is your order number?"
    notes = append_customer_reply([f"ask: {ask}"], "ORD-77819")
    assert notes == [f"ask: {ask}", "customer: ORD-77819"]
    assert append_customer_reply(notes, "ORD-77819") == notes


def test_append_customer_reply_allows_second_answer() -> None:
    ask1 = "Order number?"
    ask2 = "Customer id?"
    notes = append_customer_reply([f"ask: {ask1}"], "ORD-77819")
    notes = append_customer_reply(
        notes + ["lookup_order_by_order_id: order_id=ORD-77819", f"ask: {ask2}"],
        "CUS-1842",
    )
    assert notes[-1] == "customer: CUS-1842"
