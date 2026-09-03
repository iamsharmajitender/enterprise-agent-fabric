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
    """Return the hydrated-tools index to continue from after a gate resumes.

    Always continues at the next stage after the gate (linear). For KYC-style
    branch workflows that is typically the gated write (``activate_account``),
    then the shared merge stage (``summarize``). Do not jump to merge and skip
    the write — approve must be allowed to run the following side-effect stage.
    """
    return gate_index + 1


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
