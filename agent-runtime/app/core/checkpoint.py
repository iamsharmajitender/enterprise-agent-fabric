from typing import Any

from app.graph.branch import branch_slot_key, resolve_branch_target


def tool_stage_id(tool: dict[str, Any]) -> str:
    return str(tool.get("workflow_stage_id") or tool.get("id") or "")


def next_stage_index(
    tools: list[dict[str, Any]],
    completed_step: int,
    slots: dict[str, Any],
) -> int:
    """Return the hydrated-tools index to run next after completed_step finishes."""
    if completed_step < 0 or completed_step >= len(tools):
        return completed_step + 1
    tool = tools[completed_step]
    branch = tool.get("branch")
    if isinstance(branch, dict) and branch:
        slot_body = slots.get(branch_slot_key(tool)) or {}
        if not isinstance(slot_body, dict):
            slot_body = {}
        target = resolve_branch_target(branch, slot_body)
        for index, candidate in enumerate(tools):
            if tool_stage_id(candidate) == target:
                return index
    return completed_step + 1


def checkpoint_resume_index(
    checkpoint: dict[str, Any] | None,
    tools: list[dict[str, Any]],
    slots: dict[str, Any],
) -> int | None:
    """Resolve the graph start index from a persisted checkpoint."""
    if not isinstance(checkpoint, dict) or not checkpoint:
        return None
    if checkpoint.get("waiting_for") == "human_gate":
        raw = checkpoint.get("resume_index")
        return int(raw) if raw is not None else None
    if checkpoint.get("resume_index") is not None:
        return int(checkpoint["resume_index"])
    if checkpoint.get("step") is None:
        return None
    return next_stage_index(tools, int(checkpoint["step"]), slots)


def loop_resume_step(checkpoint: dict[str, Any] | None) -> int:
    """Pattern 1 loop iteration to start from after a checkpointed step."""
    if not isinstance(checkpoint, dict) or checkpoint.get("step") is None:
        return 0
    return int(checkpoint["step"]) + 1


def parse_checkpoint_resume(body: dict[str, Any] | None) -> bool:
    """True when the body asks to continue a failed checkpointed run."""
    if not isinstance(body, dict):
        return False
    if body.get("resume") is True:
        return True
    return body == {}


def checkpoint_goal(checkpoint: dict[str, Any] | None) -> dict[str, Any]:
    """Original ingress goal stored on the checkpoint blob."""
    if not isinstance(checkpoint, dict):
        return {}
    goal = checkpoint.get("goal")
    return dict(goal) if isinstance(goal, dict) else {}
