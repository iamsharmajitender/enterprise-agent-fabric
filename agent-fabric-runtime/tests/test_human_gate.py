from app.graph.human_gate import (
    HumanGateWaiting,
    gate_packet_present,
    parse_gate_packet,
    resume_index_after_gate,
)


def test_resume_index_after_gate_linear() -> None:
    tools = [
        {"id": "a", "workflow_stage_id": "a"},
        {"id": "gate", "workflow_stage_id": "manual_review", "stage_type": "human_gate"},
        {"id": "write", "workflow_stage_id": "post_refund"},
    ]
    assert resume_index_after_gate(tools, 1) == 2


def test_resume_index_after_gate_branch_target_merges() -> None:
    tools = [
        {
            "id": "risk",
            "workflow_stage_id": "risk_score",
            "branch": {"high": "manual_review", "low": "activate_account"},
        },
        {"id": "gate", "workflow_stage_id": "manual_review", "stage_type": "human_gate"},
        {"id": "activate", "workflow_stage_id": "activate_account"},
        {"id": "summarize", "workflow_stage_id": "summarize"},
    ]
    assert resume_index_after_gate(tools, 1) == 3


def test_parse_gate_packet_rejects_message_only() -> None:
    assert parse_gate_packet({"message": "yes"}) is None
    assert parse_gate_packet({"decision": "approve", "reviewer_id": "ops-1"}) == {
        "decision": "approve",
        "reviewer_id": "ops-1",
    }


def test_gate_packet_present() -> None:
    assert gate_packet_present({"manual_review": {"decision": "approve"}}, "manual_review") is True
    assert gate_packet_present({}, "manual_review") is False


def test_human_gate_waiting_carries_resume_index() -> None:
    exc = HumanGateWaiting(
        stage_id="manual_review",
        gate_index=1,
        resume_index=3,
        state={"goal": {}, "notes": [], "slots": {}},
    )
    assert exc.resume_index == 3
    assert "human_gate" in str(exc)
