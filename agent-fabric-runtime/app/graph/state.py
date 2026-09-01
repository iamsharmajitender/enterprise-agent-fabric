from typing import Any, TypedDict

from app.agents.prefetch import prefetch_pack_text


class GraphState(TypedDict, total=False):
    result: str
    goal: dict[str, Any]
    notes: list[str]
    slots: dict[str, Any]
    correlation_id: str
    step: int
    _resume_loop_step: int
    _route: str
    _tool_id: str
    _call_args: dict[str, Any]


def mapping(value: Any) -> dict[str, Any]:
    """Treat a non-dict as empty so stage fields stay optional."""
    return value if isinstance(value, dict) else {}


def slots(state: GraphState) -> dict[str, Any]:
    """Copy prior stage slots from graph state."""
    raw = state.get("slots")
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


def append_unique_note(notes: list[str], note: str) -> list[str]:
    """Append a note unless it duplicates the previous entry."""
    text = (note or "").strip()
    if not text:
        return list(notes)
    if notes and notes[-1] == text:
        return list(notes)
    return list(notes) + [text]


def _stage_note_id(note: str) -> str | None:
    """Return the stage id prefix for notes like ``lookup_order: field=value``."""
    if note.startswith(("customer:", "tool error")):
        return None
    head, sep, _ = note.partition(": ")
    if not sep or " " in head or not head:
        return None
    return head


def pending_customer_ask_message(notes: list[str]) -> str | None:
    """Return the latest ask: note that still has no following customer: reply."""
    pending: str | None = None
    for note in notes:
        text = (note or "").strip()
        if text.startswith("customer:"):
            pending = None
            continue
        if text.startswith("ask:"):
            pending = text[len("ask:") :].strip()
    return pending


def append_customer_reply(notes: list[str], reply: str) -> list[str]:
    """Append ``customer: {reply}`` once per pending ask; idempotent on resume retries."""
    text = (reply or "").strip()
    if not text:
        raise ValueError("customer reply is required")
    note = f"customer: {text}"
    updated = list(notes)
    if updated and updated[-1] == note:
        return updated
    if pending_customer_ask_message(updated) is None:
        for prior in reversed(updated):
            if prior.startswith("customer:"):
                return updated if prior == note else append_unique_note(updated, note)
            if prior.startswith("ask:"):
                break
        return updated
    return append_unique_note(updated, note)


def compress_notes_for_llm(notes: list[str]) -> list[str]:
    """Keep the latest stage note per tool and drop consecutive duplicates."""
    if not notes:
        return []
    last_index: dict[str, int] = {}
    for idx, note in enumerate(notes):
        stage_id = _stage_note_id(note)
        if stage_id:
            last_index[stage_id] = idx
    compressed: list[str] = []
    for idx, note in enumerate(notes):
        stage_id = _stage_note_id(note)
        if stage_id:
            if last_index.get(stage_id) != idx:
                continue
        elif compressed and compressed[-1] == note:
            continue
        compressed.append(note)
    return compressed


def slot_has_result(slot_map: dict[str, Any], stage_id: str) -> bool:
    """True when a prior stage already wrote a non-empty slot body."""
    body = slot_map.get(stage_id)
    return isinstance(body, dict) and bool(body)


def user_blob(goal: dict[str, Any], notes: list[str], slot_map: dict[str, Any] | None = None) -> str:
    """Build the LLM user message from the goal, prefetch pack, and prior stage notes."""
    lines = [f"goal: {goal}"]
    pack = prefetch_pack_text(slot_map)
    if pack:
        lines.append("packed chunks:")
        lines.extend(f"- {line}" for line in pack.splitlines())
    display_notes = compress_notes_for_llm(notes)
    if display_notes:
        lines.append("prior stage outputs:")
        lines.extend(f"- {note}" for note in display_notes)
    return "\n".join(lines)


def initial_loop_state(state: GraphState) -> GraphState:
    """Normalize invoke input for the Pattern 1 agent loop."""
    if state.get("step") is not None:
        step = int(state["step"])
    else:
        step = int(state.get("_resume_loop_step") or 0)
    return {
        "result": str(state.get("result") or ""),
        "goal": dict(mapping(state.get("goal"))),
        "notes": list(state.get("notes") or []),
        "slots": slots(state),
        "correlation_id": str(state.get("correlation_id") or ""),
        "step": step,
    }
