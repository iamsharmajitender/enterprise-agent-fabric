"""Pattern 1 handoff auto-complete and idempotent replay."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app import telemetry
from app.graph.payload import schema_properties
from app.graph.state import GraphState, slots
from app.graph.subagent_gate import subagent_result_present


def is_handoff_tool(pinned: dict[str, Any]) -> bool:
    """True when the capability output schema declares a handoff_id field."""
    schema = pinned.get("output_schema")
    if not isinstance(schema, dict):
        return False
    return "handoff_id" in schema_properties(schema)


def handoff_from_slots(slot_map: dict[str, Any]) -> tuple[str, str] | None:
    """Return (stage_id, handoff_id) for the first slot that recorded a handoff."""
    for stage_id, body in slot_map.items():
        if not isinstance(body, dict):
            continue
        hid = str(body.get("handoff_id") or "").strip()
        if hid:
            return stage_id, hid
    return None


def subagent_joins_pending(slot_map: dict[str, Any]) -> bool:
    """True when a kind=agent child was started but has not yet joined."""
    for stage_id, body in slot_map.items():
        if not isinstance(body, dict):
            continue
        if not str(body.get("correlation_id") or "").strip():
            continue
        if subagent_result_present(slot_map, stage_id):
            continue
        return True
    return False


def handoff_completion_message(slot_map: dict[str, Any], stage_id: str, handoff_id_value: str) -> str:
    """Customer-facing message after a successful handoff."""
    body = slot_map.get(stage_id)
    if isinstance(body, dict):
        text = str(body.get("text") or "").strip()
        if text and handoff_id_value in text:
            return (
                f"{text} I've escalated your case to our specialist team. "
                f"Please keep reference {handoff_id_value} for follow-up."
            )
        if text:
            return text
    return (
        f"I've escalated your case to our specialist team. "
        f"Your reference is {handoff_id_value}. Someone will follow up shortly."
    )


def complete_after_handoff(
    current: GraphState,
    step: int,
    stage_id: str,
    handoff_id_value: str,
    on_stage: Callable[[int, str, GraphState], None] | None,
) -> GraphState:
    """End the agent loop after a successful handoff when no subagent joins are pending."""
    message = handoff_completion_message(slots(current), stage_id, handoff_id_value)
    finished: GraphState = {
        **current,
        "result": message,
        "notes": list(current.get("notes") or []) + [message],
        "_route": "end",
    }
    telemetry.emit_stage_started("respond", "synthesis", "")
    if on_stage is not None:
        on_stage(step, "respond", finished)
    return finished


def try_complete_existing_handoff(
    current: GraphState,
    step: int,
    on_stage: Callable[[int, str, GraphState], None] | None,
) -> GraphState | None:
    """Skip further LLM turns when a handoff already succeeded and joins are clear."""
    slot_map = slots(current)
    found = handoff_from_slots(slot_map)
    if found is None or subagent_joins_pending(slot_map):
        return None
    stage_id, hid = found
    return complete_after_handoff(current, step, stage_id, hid, on_stage)


def replay_idempotent_handoff(
    current: GraphState,
    step: int,
    tool_id: str,
    on_stage: Callable[[int, str, GraphState], None] | None,
) -> GraphState:
    """Do not POST handoff again; complete or note when a handoff already exists."""
    slot_map = slots(current)
    found = handoff_from_slots(slot_map)
    if found is None:
        raise RuntimeError(f"{tool_id} replay requires an existing handoff_id")
    stage_id, hid = found
    if subagent_joins_pending(slot_map):
        note = f"Handoff {hid} is already open; waiting on specialist tasks to finish."
        replayed: GraphState = {
            **current,
            "result": note,
            "notes": list(current.get("notes") or []) + [note],
            "step": step + 1,
        }
        if on_stage is not None:
            on_stage(step, tool_id, replayed)
        return replayed
    return complete_after_handoff(current, step + 1, stage_id, hid, on_stage)
