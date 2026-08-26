from app.agents.audit_client import hydrate_snapshot, run_terminal, sha256_digest, stage_completed


def test_sha256_digest_stable() -> None:
    assert sha256_digest("fee").startswith("sha256:")
    assert sha256_digest("fee") == sha256_digest("fee")


def test_hydrate_and_terminal_envelope() -> None:
    snap = hydrate_snapshot(
        "corr-1",
        "sess-1",
        "fee_explain",
        "2026.08.1",
        [{"id": "account_fee_lookup", "version": "2026.08.1", "invoke": {"url": "http://x/fee"}}],
        manifest_id="fee_explain_v1",
        manifest_version="2026.08.1",
    )
    assert snap["producer"] == "ar"
    assert snap["event_type"] == "hydrate.snapshot"
    assert snap["payload"]["capabilities"][0]["capability_id"] == "account_fee_lookup"
    term = run_terminal("corr-1", "sess-1", "completed", "fee_explain", "2026.08.1")
    assert term["event_type"] == "run.terminal"
    stage = stage_completed("corr-1", "sess-1", "account_fee_lookup", "none", "completed", 3, {}, {"ok": True})
    assert stage["event_type"] == "stage.completed"
