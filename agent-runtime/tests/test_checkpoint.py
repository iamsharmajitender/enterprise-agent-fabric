from app.core.checkpoint import (
    checkpoint_goal,
    checkpoint_resume_index,
    loop_resume_step,
    next_stage_index,
    parse_checkpoint_resume,
    tool_stage_id,
)


def test_next_stage_index_linear() -> None:
    tools = [
        {"id": "a", "workflow_stage_id": "a"},
        {"id": "b", "workflow_stage_id": "b"},
    ]
    assert next_stage_index(tools, 0, {}) == 1


def test_next_stage_index_after_branch() -> None:
    tools = [
        {
            "id": "risk",
            "workflow_stage_id": "risk_score",
            "branch": {"high": "manual_review", "low": "activate_account"},
        },
        {"id": "gate", "workflow_stage_id": "manual_review"},
        {"id": "activate", "workflow_stage_id": "activate_account"},
        {"id": "summarize", "workflow_stage_id": "summarize"},
    ]
    assert next_stage_index(tools, 0, {"risk": {"risk": "low"}}) == 2
    assert next_stage_index(tools, 0, {"risk": {"risk": "high"}}) == 1


def test_checkpoint_resume_index_uses_saved_resume_index() -> None:
    tools = [{"id": "a"}, {"id": "b"}]
    assert checkpoint_resume_index({"step": 0, "resume_index": 2}, tools, {}) == 2


def test_parse_checkpoint_resume() -> None:
    assert parse_checkpoint_resume({}) is True
    assert parse_checkpoint_resume({"resume": True}) is True
    assert parse_checkpoint_resume({"message": "hi"}) is False


def test_checkpoint_goal() -> None:
    assert checkpoint_goal({"goal": {"doc_id": "d-1"}}) == {"doc_id": "d-1"}


def test_loop_resume_step() -> None:
    assert loop_resume_step({"step": 1}) == 2
    assert loop_resume_step(None) == 0


def test_tool_stage_id_prefers_workflow_stage_id() -> None:
    assert tool_stage_id({"id": "cap", "workflow_stage_id": "stage"}) == "stage"
