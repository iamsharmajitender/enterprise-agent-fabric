from app.graph.branch import branch_choice, resolve_branch_target


def test_branch_choice_reads_risk_field() -> None:
    assert branch_choice({"risk": "low", "text": "ok"}, {"high": "manual_review", "low": "activate_account"}) == "low"


def test_branch_choice_fails_on_unknown_value() -> None:
    try:
        branch_choice({"risk": "medium"}, {"high": "manual_review", "low": "activate_account"})
    except RuntimeError as exc:
        assert "no known key" in str(exc)
        return
    raise AssertionError("expected branch failure")


def test_resolve_branch_target_returns_stage_id() -> None:
    assert (
        resolve_branch_target(
            {"high": "manual_review", "low": "activate_account"},
            {"risk": "high"},
        )
        == "manual_review"
    )
