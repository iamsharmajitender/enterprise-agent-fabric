from app.agents.audit_client import hydrate_snapshot, run_terminal, sha256_digest, stage_completed


def test_sha256_digest_stable() -> None:
    assert sha256_digest("fee").startswith("sha256:")
    assert sha256_digest("fee") == sha256_digest("fee")


def test_hydrate_and_terminal_envelope() -> None:
    snap = hydrate_snapshot(
        "corr-1",
        "sess-1",
        "shopassist_case",
        "2026.08.1",
        [
            {
                "id": "account_fee_lookup",
                "version": "2026.08.1",
                "invoke": {"url": "http://x/fee"},
            }
        ],
        manifest_id="shopassist_case_v1",
        manifest_version="2026.08.1",
        prompt_id="shopassist_case",
    )
    assert snap["producer"] == "ar"
    assert snap["event_type"] == "hydrate.snapshot"
    assert snap["payload"]["capabilities"][0]["capability_id"] == "account_fee_lookup"
    assert snap["payload"]["prompt_id"] == "shopassist_case"
    assert snap["payload"]["retrieval"] is None
    term = run_terminal("corr-1", "sess-1", "completed", "shopassist_case", "2026.08.1")
    assert term["event_type"] == "run.terminal"
    stage = stage_completed("corr-1", "sess-1", "account_fee_lookup", "none", "completed", 3, {}, {"ok": True})
    assert stage["event_type"] == "stage.completed"


def test_hydrate_snapshot_excludes_synthetic_stages_includes_retrieval() -> None:
    snap = hydrate_snapshot(
        "corr-od",
        "sess-od",
        "overdraft_fee_qa",
        "2026.08.1",
        [
            {"id": "prefetch", "llm_role": "none", "invoke": {}},
            {"id": "overdraft_fee_qa", "llm_role": "synthesis", "invoke": {}},
            {
                "id": "account_fee_lookup",
                "version": "2026.08.1",
                "invoke": {"url": "http://x/fee"},
            },
        ],
        prompt_id="overdraft_fee_qa",
        retrieval={
            "mode": "deterministic_prefetch",
            "scope": ["fee-schedule", "product-disclosure"],
        },
    )
    payload = snap["payload"]
    assert payload["prompt_id"] == "overdraft_fee_qa"
    assert payload["retrieval"] == {
        "mode": "deterministic_prefetch",
        "scope": ["fee-schedule", "product-disclosure"],
    }
    assert [c["capability_id"] for c in payload["capabilities"]] == ["account_fee_lookup"]
