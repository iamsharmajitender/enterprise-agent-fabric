from app.core.memory import (
    checkpoint_payload,
    memory_profile,
    notes_from_working,
    persist_stage,
    save_loop,
    save_working,
    working_payload,
)
from tests.in_memory_store import InMemoryRunStore
from app.core.state import RunPin


def test_memory_profile_reads_catalogue_object() -> None:
    assert memory_profile({"memory_profile": {"working": "session"}}) == {"working": "session"}
    assert memory_profile({}) == {}
    assert memory_profile(None) == {}


def test_save_flags() -> None:
    assert save_working({"working": "session"}) is True
    assert save_working({"working": "none"}) is False
    assert save_loop({"loop": "checkpoint"}) is True
    assert save_loop({"loop": "none"}) is False
    assert save_loop({}) is False


def test_persist_stage_writes_working_and_checkpoint() -> None:
    store = InMemoryRunStore()
    pin = RunPin(
        correlation_id="corr-1",
        idempotency_key="k",
        session_id="sess-1",
        route_id="fee_explain",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=[],
        status="running",
    )
    store.insert(pin)
    persist_stage(
        store,
        "corr-1",
        {"working": "session", "loop": "checkpoint"},
        1,
        "clause_search",
        {"notes": ["hit"], "slots": {"ocr": {"text": "x"}}, "result": "hit", "goal": {"claim_id": "clm-1"}},
        tools=[{"id": "ocr"}, {"id": "clause_search"}, {"id": "memo"}],
    )
    saved = store.get("corr-1")
    assert saved is not None
    assert saved.working == working_payload(["hit"], {"ocr": {"text": "x"}})
    expected = checkpoint_payload(1, "clause_search", "hit", {"claim_id": "clm-1"})
    expected["resume_index"] = 2
    assert saved.checkpoint == expected


def test_persist_stage_skips_when_profile_is_none() -> None:
    store = InMemoryRunStore()
    pin = RunPin(
        correlation_id="corr-2",
        idempotency_key="k2",
        session_id="sess-2",
        route_id="llm_pipeline",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=[],
        status="running",
    )
    store.insert(pin)
    persist_stage(store, "corr-2", {}, 0, "extract", {"notes": ["x"], "result": "x", "goal": {}})
    saved = store.get("corr-2")
    assert saved is not None
    assert saved.working is None
    assert saved.checkpoint is None


def test_working_payload_includes_empty_slots() -> None:
    assert working_payload(["a"]) == {"notes": ["a"], "slots": {}}


def test_slots_from_working() -> None:
    from app.core.memory import slots_from_working

    assert slots_from_working({"notes": ["a"], "slots": {"ocr": {"text": "x"}}}) == {
        "ocr": {"text": "x"}
    }
    assert slots_from_working({"notes": ["a"]}) == {}
    assert slots_from_working(None) == {}


def test_notes_from_working() -> None:
    assert notes_from_working({"notes": ["a", "b"]}) == ["a", "b"]
    assert notes_from_working(None) == []
    assert notes_from_working({"notes": "bad"}) == []
