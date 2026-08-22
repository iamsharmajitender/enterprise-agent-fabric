from typing import Any

from app.core.state import RunStore


def memory_profile(row: dict[str, Any] | None) -> dict[str, Any]:
    """Read the catalogue `memory_profile` object, or {}."""
    raw = (row or {}).get("memory_profile")
    return raw if isinstance(raw, dict) else {}


def save_working(profile: dict[str, Any]) -> bool:
    """True when stage notes must be flushed to `runtime.runs.working`."""
    return str(profile.get("working") or "").strip() == "session"


def save_loop(profile: dict[str, Any]) -> bool:
    """True when each stage must write `runtime.runs.checkpoint`."""
    return str(profile.get("loop") or "").strip() == "checkpoint"


def working_payload(notes: list[str] | None) -> dict[str, Any]:
    """JSON stored in `runtime.runs.working`."""
    return {"notes": list(notes or [])}


def checkpoint_payload(
    step: int, stage_id: str, result: str, goal: dict[str, Any]
) -> dict[str, Any]:
    """JSON stored in `runtime.runs.checkpoint` after a completed stage."""
    return {"step": step, "stage_id": stage_id, "result": result, "goal": dict(goal)}


def persist_stage(
    store: RunStore,
    correlation_id: str,
    profile: dict[str, Any],
    step: int,
    stage_id: str,
    state: dict[str, Any],
) -> None:
    """Flush working notes and/or loop checkpoint after one graph stage."""
    notes = list(state.get("notes") or [])
    result = str(state.get("result") or "")
    goal = state.get("goal") if isinstance(state.get("goal"), dict) else {}
    working = working_payload(notes) if save_working(profile) else None
    checkpoint = (
        checkpoint_payload(step, stage_id, result, goal) if save_loop(profile) else None
    )
    if working is None and checkpoint is None:
        return
    store.save_progress(correlation_id, working=working, checkpoint=checkpoint)


def notes_from_working(working: dict[str, Any] | None) -> list[str]:
    """Reload persisted working notes for the next invoke or turn."""
    if not isinstance(working, dict):
        return []
    notes = working.get("notes")
    if not isinstance(notes, list):
        return []
    return [str(note) for note in notes]
