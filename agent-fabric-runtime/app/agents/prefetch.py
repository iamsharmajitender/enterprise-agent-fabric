from typing import Any, Protocol


class PrefetchPort(Protocol):
    def search(self, url: str, collection: str, goal: dict[str, Any]) -> list[dict[str, Any]]: ...


def retrieval_mode(retrieval: dict[str, Any] | None) -> str:
    """Read catalogue retrieval.mode, or empty when absent."""
    if not isinstance(retrieval, dict):
        return ""
    return str(retrieval.get("mode") or "").strip()


def retrieval_scope(retrieval: dict[str, Any] | None) -> list[str]:
    """Read catalogue retrieval.scope corpus ids."""
    if not isinstance(retrieval, dict):
        return []
    scope = retrieval.get("scope")
    if not isinstance(scope, list):
        return []
    return [str(item) for item in scope if str(item).strip()]


def is_prefetch_stage(pinned: dict[str, Any], retrieval: dict[str, Any] | None) -> bool:
    """True for workflow prefetch placeholders on deterministic_prefetch routes."""
    role = str(pinned.get("llm_role") or "none").strip() or "none"
    if role != "none":
        return False
    invoke = pinned.get("invoke") if isinstance(pinned.get("invoke"), dict) else {}
    if str(invoke.get("url") or "").strip():
        return False
    if str(pinned.get("id") or "") != "prefetch":
        return False
    return retrieval_mode(retrieval) == "deterministic_prefetch"


def packed_note(chunks: list[dict[str, Any]]) -> str:
    """Short LLM-facing summary of packed corpus chunks."""
    lines: list[str] = []
    for chunk in chunks:
        corpus_id = str(chunk.get("corpus_id") or "corpus")
        chunk_id = str(chunk.get("id") or "chunk")
        text = str(chunk.get("text") or "").strip()
        if text:
            lines.append(f"[{corpus_id}:{chunk_id}] {text}")
    return "\n".join(lines)


PREFETCH_SLOT_ID = "prefetch"


def prefetch_chunks(slots: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Read chunk objects from the prefetch working slot, if present."""
    if not isinstance(slots, dict):
        return []
    slot = slots.get(PREFETCH_SLOT_ID)
    if not isinstance(slot, dict):
        return []
    raw = slot.get("chunks")
    if not isinstance(raw, list):
        return []
    return [chunk for chunk in raw if isinstance(chunk, dict)]


def prefetch_pack_text(slots: dict[str, Any] | None) -> str:
    """Packed prose derived from the prefetch slot."""
    return packed_note(prefetch_chunks(slots))


def require_prefetch_pack(
    slots: dict[str, Any] | None,
    retrieval: dict[str, Any] | None,
    stage_id: str,
    *,
    expects_prefetch: bool,
) -> None:
    """Fail closed when a downstream stage runs without a prefetch pack on prefetch routes."""
    if not expects_prefetch:
        return
    if retrieval_mode(retrieval) != "deterministic_prefetch":
        return
    if stage_id == PREFETCH_SLOT_ID:
        return
    if not prefetch_pack_text(slots):
        raise RuntimeError("prefetch pack required but prefetch slot is empty")


def prefetch_corpus_stage_id(corpus_id: str) -> str:
    """Audit / slot key for one corpus search inside the prefetch stage."""
    return f"{PREFETCH_SLOT_ID}:{corpus_id}"


def run_prefetch(
    catalogue: Any,
    prefetch: PrefetchPort,
    retrieval: dict[str, Any],
    goal: dict[str, Any],
) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    """POST each scoped corpus and return a slot body, packed note, and per-corpus hits."""
    scope = retrieval_scope(retrieval)
    if not scope:
        raise RuntimeError("prefetch scope empty")

    chunks: list[dict[str, Any]] = []
    per_corpus: list[dict[str, Any]] = []
    for corpus_id in scope:
        corpus = catalogue.get_corpus(corpus_id)
        status = str(corpus.get("status") or "").strip()
        if status != "published":
            raise RuntimeError(f"corpus {corpus_id!r} not published")
        url = str(corpus.get("url") or "").strip()
        collection = str(corpus.get("collection") or corpus_id).strip()
        if not url or not collection:
            raise RuntimeError(f"corpus {corpus_id!r} missing url or collection")
        found: list[dict[str, Any]] = []
        for chunk in prefetch.search(url, collection, goal):
            if isinstance(chunk, dict):
                tagged = {**chunk, "corpus_id": corpus_id}
                found.append(tagged)
                chunks.append(tagged)
        per_corpus.append({"corpus_id": corpus_id, "chunks": found})

    if not chunks:
        raise RuntimeError("prefetch returned no chunks")

    note = packed_note(chunks)
    if not note:
        raise RuntimeError("prefetch returned empty pack")
    return {"chunks": chunks}, note, per_corpus
