"""Skip repeat HTTP calls when a Pattern 1 tool slot is already populated."""

from __future__ import annotations

from typing import Any

from app.graph.state import GraphState, append_unique_note, slot_has_result


def replay_completed_tool(
    current: GraphState,
    step: int,
    tool_id: str,
) -> GraphState:
    """Do not invoke HTTP again; nudge the LLM once to pick the next step."""
    note = (
        f"{tool_id}: already completed; use prior stage outputs and "
        "choose the next tool or done."
    )
    return {
        **current,
        "notes": append_unique_note(list(current.get("notes") or []), note),
        "step": step + 1,
    }


def should_replay_completed_tool(
    slot_map: dict[str, Any],
    tool_id: str,
    *,
    is_handoff: bool,
) -> bool:
    return not is_handoff and slot_has_result(slot_map, tool_id)
