from app.agents.prefetch import is_prefetch_stage, packed_note, run_prefetch
from tests.conftest import FakeCatalogue


class FakePrefetch:
    def __init__(self, chunks: list[dict] | None = None) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        if chunks is None:
            self._chunks = [{"id": "policy-engine-1", "text": "Refund window is 30 days."}]
        else:
            self._chunks = chunks

    def search(self, url: str, collection: str, goal: dict) -> list[dict]:
        self.calls.append((url, collection, goal))
        return list(self._chunks)


def test_is_prefetch_stage_requires_prefetch_id_and_mode() -> None:
    pinned = {"id": "prefetch", "llm_role": "none", "invoke": {}}
    retrieval = {"mode": "deterministic_prefetch", "scope": ["policy-engine"]}
    assert is_prefetch_stage(pinned, retrieval) is True
    assert is_prefetch_stage({**pinned, "id": "generate"}, retrieval) is False
    assert is_prefetch_stage(pinned, {"mode": "tool", "scope": ["policy-engine"]}) is False
    assert is_prefetch_stage(pinned, None) is False


def test_run_prefetch_merges_scope_and_builds_note() -> None:
    catalogue = FakeCatalogue()
    catalogue.corpora = {
        "policy-engine": {
            "corpus_id": "policy-engine",
            "url": "http://agent-mocks:3010/v1/search/assistant",
            "collection": "policy-engine",
            "status": "published",
        }
    }
    prefetch = FakePrefetch()
    slot, note, per_corpus = run_prefetch(
        catalogue,
        prefetch,
        {"mode": "deterministic_prefetch", "scope": ["policy-engine"]},
        {"topic": "refunds"},
    )
    assert prefetch.calls == [
        ("http://agent-mocks:3010/v1/search/assistant", "policy-engine", {"topic": "refunds"})
    ]
    assert slot["chunks"][0]["corpus_id"] == "policy-engine"
    assert "Refund window" in note
    assert per_corpus == [
        {
            "corpus_id": "policy-engine",
            "chunks": [{"id": "policy-engine-1", "text": "Refund window is 30 days.", "corpus_id": "policy-engine"}],
        }
    ]

def test_run_prefetch_fails_on_unpublished_corpus() -> None:
    catalogue = FakeCatalogue()
    catalogue.corpora = {
        "research-index": {
            "corpus_id": "research-index",
            "url": "http://agent-mocks:3010/v1/search/assistant",
            "collection": "research-index",
            "status": "draft",
        }
    }
    try:
        run_prefetch(
            catalogue,
            FakePrefetch(),
            {"mode": "deterministic_prefetch", "scope": ["research-index"]},
            {},
        )
    except RuntimeError as exc:
        assert "not published" in str(exc)
        return
    raise AssertionError("expected unpublished corpus failure")


def test_packed_note_formats_chunks() -> None:
    note = packed_note(
        [
            {"corpus_id": "policy-engine", "id": "pe-1", "text": "Rule one."},
            {"corpus_id": "product-faq", "id": "faq-1", "text": "Rule two."},
        ]
    )
    assert note == "[policy-engine:pe-1] Rule one.\n[product-faq:faq-1] Rule two."


def test_prefetch_pack_text_reads_slot() -> None:
    from app.agents.prefetch import prefetch_pack_text, require_prefetch_pack

    slots = {
        "prefetch": {
            "chunks": [{"corpus_id": "policy-engine", "id": "pe-1", "text": "Rule one."}]
        }
    }
    assert "Rule one." in prefetch_pack_text(slots)
    try:
        require_prefetch_pack({}, {"mode": "deterministic_prefetch"}, "generate", expects_prefetch=True)
    except RuntimeError as exc:
        assert "prefetch slot is empty" in str(exc)
        return
    raise AssertionError("expected empty prefetch pack failure")
