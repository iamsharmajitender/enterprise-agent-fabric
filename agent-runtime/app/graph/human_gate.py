from typing import Any


class HumanGateWaiting(Exception):
    """Raised when a human_gate stage needs a resume packet before continuing."""

    def __init__(
        self,
        *,
        stage_id: str,
        gate_index: int,
        resume_index: int,
        state: dict[str, Any],
    ) -> None:
        self.stage_id = stage_id
        self.gate_index = gate_index
        self.resume_index = resume_index
        self.state = state
        super().__init__(f"human_gate waiting for human input at {stage_id!r}")


def resume_index_after_gate(tools: list[dict[str, Any]], gate_index: int) -> int:
    """Return the hydrated-tools index to continue from after a gate resumes."""
    if gate_index + 1 >= len(tools):
        return gate_index + 1

    gate_stage_id = str(tools[gate_index].get("workflow_stage_id") or tools[gate_index].get("id") or "")
    branch_at = None
    branch_map: dict[str, Any] | None = None
    for index, tool in enumerate(tools):
        branch = tool.get("branch")
        if isinstance(branch, dict) and branch:
            branch_at = index
            branch_map = branch
            break
    if branch_at is None or branch_map is None:
        return gate_index + 1

    branch_targets = {str(value) for value in branch_map.values()}
    if gate_stage_id not in branch_targets:
        return gate_index + 1

    for index in range(branch_at + 1, len(tools)):
        stage_id = str(tools[index].get("workflow_stage_id") or tools[index].get("id") or "")
        if stage_id not in branch_targets:
            return index
    raise RuntimeError("branch workflow missing merge stage after branch targets")


def human_gate_slot_key(pinned: dict[str, Any]) -> str:
    """Slot id written when a human packet is merged on resume."""
    return str(pinned.get("workflow_stage_id") or pinned.get("id") or "")


def gate_packet_present(slots: dict[str, Any], stage_id: str) -> bool:
    """True when the gate stage already has a merged human packet."""
    body = slots.get(stage_id)
    return isinstance(body, dict) and bool(body)


def parse_gate_packet(body: dict[str, Any]) -> dict[str, Any] | None:
    """Extract a human resume packet; empty or message-only bodies stay paused."""
    if not isinstance(body, dict) or not body:
        return None
    if set(body.keys()) == {"message"}:
        return None
    decision = str(body.get("decision") or "").strip().lower()
    if not decision and len(body) <= 1 and "message" in body:
        return None
    if not decision and not any(key != "message" for key in body):
        return None
    return body
