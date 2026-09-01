import pytest

from app.agents.hydrate import HydrateError, hydrate
from tests.conftest import START_BODY, FakeCatalogue, FakeRegistry


def test_hydrate_fetches_manifest_and_each_capability() -> None:
    catalogue = FakeCatalogue()
    registry = FakeRegistry()
    tools = hydrate(START_BODY, catalogue, registry)
    assert catalogue.route_calls == [("pattern1_case", "2026.08.1")]
    assert registry.manifest_calls == [("pattern1_case", "2026.08.1")]
    assert registry.capability_calls == [
        ("fetch_record", "1.0.0"),
        ("open_handoff", "1.0.0"),
    ]
    assert [tool["id"] for tool in tools] == ["fetch_record", "open_handoff"]
    assert tools[0]["llm_role"] == "none"
    assert catalogue.decide_calls == []
    assert catalogue.workflow_calls == []


def test_hydrate_attaches_workflow_llm_roles() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "claims_adjudicate",
            "route_version": "2026.08.1",
            "tool_manifest": "claims_adjudicate",
            "tool_manifest_version": "2026.08.1",
            "workflow_id": "claims_adjudicate",
            "prompt_id": "claims_adjudicate",
        }
    )
    catalogue.workflow = {
        "stages": [
            {"tool": "policy_search", "llm_role": "none"},
            {"tool": "clause_search", "llm_role": "query_formulation"},
            {"tool": "draft_memo", "llm_role": "synthesis"},
        ]
    }
    catalogue.prompt = {
        "by_llm_role": {
            "query_formulation": {"text": "Write the clause-index query."},
            "synthesis": {"text": "Draft the claims memo from stage outputs only."},
        }
    }
    registry = FakeRegistry(
        manifest={
            "tools": [
                {"capability_id": "clause_search", "capability_version": "1.0.0"},
                {"capability_id": "draft_memo", "capability_version": "1.0.0"},
            ]
        }
    )
    tools = hydrate(
        {**START_BODY, "route_id": "claims_adjudicate"},
        catalogue,
        registry,
    )
    assert catalogue.workflow_calls == ["claims_adjudicate"]
    assert tools[0]["id"] == "clause_search"
    assert tools[0]["llm_role"] == "query_formulation"
    assert tools[0]["llm_prompt"] == "Write the clause-index query."
    assert tools[1]["id"] == "draft_memo"
    assert tools[1]["llm_role"] == "synthesis"


def test_hydrate_fails_when_capability_missing() -> None:
    with pytest.raises(HydrateError):
        hydrate(START_BODY, FakeCatalogue(), FakeRegistry(missing_capability=True))


def test_hydrate_requires_pinned_catalogue_version() -> None:
    body = {**START_BODY, "route_version": ""}
    with pytest.raises(HydrateError):
        hydrate(body, FakeCatalogue(), FakeRegistry())


def test_hydrate_fails_on_catalogue_miss() -> None:
    with pytest.raises(HydrateError):
        hydrate(START_BODY, FakeCatalogue(missing=True), FakeRegistry())


def test_hydrate_workflow_without_manifest() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "llm_pipeline",
            "route_version": "2026.08.1",
            "tool_manifest": None,
            "tool_manifest_version": None,
            "workflow_id": "llm_pipeline",
            "prompt_id": "llm_pipeline",
        }
    )
    catalogue.workflow = {
        "stages": [
            {"id": "extract", "llm_role": "classify"},
            {"id": "rewrite", "llm_role": "synthesis"},
            {"id": "format", "llm_role": "synthesis"},
        ]
    }
    catalogue.prompt = {
        "host": "Do only the current stage. Do not choose the next stage. No tools.",
        "by_llm_role": {
            "classify": {"text": "Extract the requested fields from the input only."},
            "synthesis": {"text": "Rewrite or format using the previous stage output only."},
        },
    }
    registry = FakeRegistry()
    tools = hydrate(
        {
            **START_BODY,
            "route_id": "llm_pipeline",
            "contract": {"tool_manifest": None, "manifest_version": None},
        },
        catalogue,
        registry,
    )
    assert registry.manifest_calls == []
    assert registry.capability_calls == []
    assert catalogue.workflow_calls == ["llm_pipeline"]
    assert [tool["id"] for tool in tools] == ["extract", "rewrite", "format"]
    assert [tool["llm_role"] for tool in tools] == ["classify", "synthesis", "synthesis"]
    assert tools[0]["llm_prompt"] == "Extract the requested fields from the input only."
    assert tools[1]["llm_prompt"] == "Rewrite or format using the previous stage output only."
    assert tools[0]["invoke"] == {}


def test_hydrate_prompt_only_without_manifest() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "email_summarize",
            "route_version": "2026.08.1",
            "tool_manifest": None,
            "tool_manifest_version": None,
            "prompt_id": "email_summarize",
        }
    )
    catalogue.prompt = {
        "host": "Summarize this email for the banker. No tools. Return short bullets."
    }
    registry = FakeRegistry()
    tools = hydrate(
        {
            **START_BODY,
            "route_id": "email_summarize",
            "contract": {},
        },
        catalogue,
        registry,
    )
    assert registry.manifest_calls == []
    assert len(tools) == 1
    assert tools[0]["id"] == "email_summarize"
    assert tools[0]["llm_role"] == "synthesis"
    assert tools[0]["llm_prompt"].startswith("Summarize this email")
    assert tools[0]["invoke"] == {}


def test_hydrate_prompt_only_prefetch_stage_for_pattern_0() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "overdraft_fee_qa",
            "route_version": "2026.08.1",
            "autonomy_mode": 0,
            "tool_manifest": None,
            "tool_manifest_version": None,
            "prompt_id": "overdraft_fee_qa",
            "retrieval": {
                "mode": "deterministic_prefetch",
                "scope": ["fee-schedule", "product-disclosure"],
            },
        }
    )
    catalogue.prompt = {
        "host": "Answer from prefetched chunks only. Cite chunk ids."
    }
    tools = hydrate(
        {**START_BODY, "route_id": "overdraft_fee_qa", "contract": {}},
        catalogue,
        FakeRegistry(),
    )
    assert [tool["id"] for tool in tools] == ["prefetch", "overdraft_fee_qa"]
    assert tools[0]["llm_role"] == "none"
    assert tools[1]["llm_role"] == "synthesis"


def test_hydrate_fails_without_manifest_workflow_or_prompt() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "orphan",
            "route_version": "2026.08.1",
            "tool_manifest": None,
            "tool_manifest_version": None,
        }
    )
    with pytest.raises(HydrateError, match="no manifest, workflow, or prompt"):
        hydrate({**START_BODY, "route_id": "orphan", "contract": {}}, catalogue, FakeRegistry())


def test_hydrate_appends_synthesis_when_pattern_2_is_http_only() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "account_notify",
            "route_version": "2026.08.1",
            "tool_manifest": "account_notify",
            "tool_manifest_version": "2026.08.1",
            "workflow_id": "account_notify",
            "prompt_id": "account_notify",
            "autonomy_mode": 2,
        }
    )
    catalogue.workflow = {
        "stages": [{"id": "notify", "tool": "notify_customer", "llm_role": "none"}]
    }
    catalogue.prompt = {
        "host": "Confirm the notify from stage outputs only.",
        "by_llm_role": {"synthesis": {"text": "Write the confirm from notes only."}},
    }
    registry = FakeRegistry(
        manifest={
            "tools": [
                {
                    "capability_id": "notify_customer",
                    "capability_version": "1.0.0",
                }
            ]
        },
        capability={
            "id": "notify_customer",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/notify"},
        },
    )
    tools = hydrate(
        {**START_BODY, "route_id": "account_notify"},
        catalogue,
        registry,
    )
    assert [tool["id"] for tool in tools] == ["notify_customer", "respond"]
    assert tools[0]["llm_role"] == "none"
    assert tools[1]["llm_role"] == "synthesis"
    assert tools[1]["llm_prompt"] == "Write the confirm from notes only."
    assert tools[1]["invoke"] == {}


def test_hydrate_appends_synthesis_when_only_query_formulation_is_present() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "clause_lookup",
            "route_version": "2026.08.1",
            "tool_manifest": "clause_lookup",
            "tool_manifest_version": "2026.08.1",
            "workflow_id": "clause_lookup",
            "prompt_id": "clause_lookup",
            "autonomy_mode": 2,
        }
    )
    catalogue.workflow = {
        "stages": [
            {
                "id": "clause_search",
                "tool": "clause_search",
                "llm_role": "query_formulation",
            }
        ]
    }
    catalogue.prompt = {
        "host": "Do only the current stage. Do not invent clauses.",
        "by_llm_role": {
            "query_formulation": {"text": "Write the clause-index query from the goal only."},
            "synthesis": {"text": "Explain the retrieved clause in plain language."},
        },
    }
    registry = FakeRegistry(
        manifest={
            "tools": [
                {
                    "capability_id": "clause_search",
                    "capability_version": "1.0.0",
                }
            ]
        },
        capability={
            "id": "clause_search",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/clauses/search"},
        },
    )
    tools = hydrate(
        {**START_BODY, "route_id": "clause_lookup"},
        catalogue,
        registry,
    )
    assert [tool["id"] for tool in tools] == ["clause_search", "respond"]
    assert tools[0]["llm_role"] == "query_formulation"
    assert tools[1]["llm_role"] == "synthesis"
    assert tools[1]["llm_prompt"] == "Explain the retrieved clause in plain language."


def test_hydrate_purchase_refund_classify_json_prompt() -> None:
    """extract_fields is on the manifest so classify is a graph node; output_schema binds JSON."""
    catalogue = FakeCatalogue(
        {
            "route_id": "purchase_refund",
            "route_version": "2026.08.1",
            "tool_manifest": "purchase_refund",
            "tool_manifest_version": "2026.08.1",
            "workflow_id": "purchase_refund",
            "prompt_id": "purchase_refund",
            "output_schema_id": "receipt_fields",
            "autonomy_mode": 2,
        }
    )
    catalogue.workflow = {
        "stages": [
            {"id": "ocr", "tool": "ocr_extract", "llm_role": "none"},
            {"id": "extract_fields", "tool": "extract_fields", "llm_role": "classify"},
            {"id": "match_purchase", "tool": "match_purchase", "llm_role": "none"},
            {"id": "eligibility", "tool": "refund_eligibility", "llm_role": "none"},
            {"id": "manual_review", "type": "human_gate"},
            {"id": "post_refund", "tool": "post_refund", "llm_role": "none"},
            {"id": "respond", "tool": "refund_confirm", "llm_role": "synthesis"},
        ]
    }
    json_prompt = (
        "Extract receipt fields from OCR notes and the goal only. "
        "Always emit every output_schema key. Use null when a value is not in the notes; do not invent."
    )
    catalogue.prompt = {
        "host": "Pattern 2. Do only the current stage. Do not invent a refund.",
        "by_llm_role": {
            "classify": {"text": json_prompt},
            "synthesis": {"text": "Write the user-facing refund confirm from stage outputs only."},
        },
    }
    registry = FakeRegistry(
        manifest={
            "tools": [
                {"capability_id": "ocr_extract", "capability_version": "1.2.0"},
                {"capability_id": "extract_fields", "capability_version": "1.0.0"},
                {"capability_id": "match_purchase", "capability_version": "1.0.0"},
                {"capability_id": "refund_eligibility", "capability_version": "1.0.0"},
                {"capability_id": "post_refund", "capability_version": "1.0.0"},
                {"capability_id": "refund_confirm", "capability_version": "1.0.0"},
            ]
        }
    )
    tools = hydrate(
        {**START_BODY, "route_id": "purchase_refund"},
        catalogue,
        registry,
    )
    assert [tool["id"] for tool in tools] == [
        "ocr_extract",
        "extract_fields",
        "match_purchase",
        "refund_eligibility",
        "post_refund",
        "refund_confirm",
    ]
    assert [tool["llm_role"] for tool in tools] == [
        "none",
        "classify",
        "none",
        "none",
        "none",
        "synthesis",
    ]
    assert tools[1]["llm_prompt"] == json_prompt
    assert "host" not in tools[1]["llm_prompt"]
    assert tools[-1]["llm_prompt"].startswith("Write the user-facing refund confirm")


def test_hydrate_kyc_onboarding_uses_workflow_order_when_branch_present() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "kyc_onboarding",
            "route_version": "2026.08.1",
            "tool_manifest": "kyc_onboarding_tools",
            "tool_manifest_version": "2026.08.1",
            "workflow_id": "kyc_onboarding",
            "prompt_id": "kyc_onboarding",
            "autonomy_mode": 2,
        }
    )
    catalogue.workflow = {
        "stages": [
            {"id": "collect_docs", "tool": "doc_intake", "llm_role": "none"},
            {"id": "identity_check", "tool": "id_verify", "llm_role": "none"},
            {"id": "sanctions_screen", "tool": "sanctions_api", "llm_role": "none"},
            {
                "id": "risk_score",
                "tool": "kyc_risk_engine",
                "llm_role": "none",
                "branch": {"high": "manual_review", "low": "activate_account"},
            },
            {"id": "manual_review", "type": "human_gate"},
            {
                "id": "activate_account",
                "tool": "account_activate",
                "llm_role": "none",
                "side_effect": True,
            },
            {"id": "summarize", "llm_role": "synthesis"},
        ]
    }
    catalogue.prompt = {
        "host": "Pattern 2. Summarize KYC evidence for a human reviewer.",
        "by_llm_role": {
            "synthesis": {"text": "Summarize KYC stage outputs for a human reviewer."},
        },
    }
    registry = FakeRegistry(
        manifest={
            "tools": [
                {"capability_id": "doc_intake", "capability_version": "1.0.0"},
                {"capability_id": "id_verify", "capability_version": "1.0.0"},
                {"capability_id": "sanctions_api", "capability_version": "1.0.0"},
                {"capability_id": "kyc_risk_engine", "capability_version": "1.0.0"},
                {"capability_id": "account_activate", "capability_version": "1.0.0"},
            ]
        }
    )
    tools = hydrate(
        {**START_BODY, "route_id": "kyc_onboarding"},
        catalogue,
        registry,
    )
    assert [tool.get("workflow_stage_id") or tool["id"] for tool in tools] == [
        "collect_docs",
        "identity_check",
        "sanctions_screen",
        "risk_score",
        "manual_review",
        "activate_account",
        "summarize",
    ]
    assert tools[3]["branch"] == {"high": "manual_review", "low": "activate_account"}
    assert tools[4]["stage_type"] == "human_gate"
    assert tools[-1]["llm_role"] == "synthesis"


def test_hydrate_duplicate_charge_review_stamps_roles_and_order() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "duplicate_charge_review",
            "route_version": "2026.08.1",
            "tool_manifest": "duplicate_charge_review",
            "tool_manifest_version": "2026.08.1",
            "workflow_id": "duplicate_charge_review",
            "prompt_id": "duplicate_charge_review",
            "autonomy_mode": 2,
        }
    )
    catalogue.workflow = {
        "stages": [
            {"id": "intake", "tool": "duplicate_charge_intake", "llm_role": "classify"},
            {"id": "order_lookup", "tool": "lookup_order_by_order_id", "llm_role": "none"},
            {"id": "dup_check", "tool": "investigate_duplicate_charge", "llm_role": "none"},
            {"id": "respond", "tool": "duplicate_charge_respond", "llm_role": "synthesis"},
        ]
    }
    catalogue.prompt = {
        "host": "Pattern 2. Do only the current stage.",
        "by_llm_role": {
            "classify": {"text": "Extract order_id from the goal utterance only."},
            "synthesis": {"text": "Write the customer reply from prior stage outputs only."},
        },
    }
    registry = FakeRegistry(
        manifest={
            "tools": [
                {"capability_id": "duplicate_charge_intake", "capability_version": "1.0.0"},
                {"capability_id": "lookup_order_by_order_id", "capability_version": "1.0.0"},
                {"capability_id": "investigate_duplicate_charge", "capability_version": "1.0.0"},
                {"capability_id": "duplicate_charge_respond", "capability_version": "1.0.0"},
            ]
        }
    )
    tools = hydrate(
        {**START_BODY, "route_id": "duplicate_charge_review"},
        catalogue,
        registry,
    )
    assert [tool["id"] for tool in tools] == [
        "duplicate_charge_intake",
        "lookup_order_by_order_id",
        "investigate_duplicate_charge",
        "duplicate_charge_respond",
    ]
    assert [tool["llm_role"] for tool in tools] == ["classify", "none", "none", "synthesis"]
    assert tools[0]["llm_prompt"] == "Extract order_id from the goal utterance only."
    assert tools[-1]["llm_prompt"] == "Write the customer reply from prior stage outputs only."


def test_hydrate_ticket_triage_stamps_guided_roles() -> None:
    catalogue = FakeCatalogue(
        {
            "route_id": "ticket_triage",
            "route_version": "2026.08.1",
            "tool_manifest": "ticket_triage",
            "tool_manifest_version": "2026.08.1",
            "workflow_id": "ticket_triage",
            "prompt_id": "ticket_triage",
            "autonomy_mode": 3,
        }
    )
    catalogue.workflow = {
        "stages": [
            {
                "id": "extract",
                "tool": "parse_ticket",
                "llm_role": "none",
                "allowlist": ["parse_ticket"],
                "max_tool_calls": 2,
            },
            {
                "id": "analyse",
                "tool": "tag_intent",
                "llm_role": "none",
                "allowlist": ["parse_ticket", "tag_intent"],
                "max_tool_calls": 4,
            },
            {
                "id": "reply",
                "tool": "draft_reply",
                "llm_role": "none",
                "allowlist": ["draft_reply"],
                "max_tool_calls": 2,
            },
        ]
    }
    catalogue.prompt = {
        "host": "Pattern 3. Outer stages are fixed.",
    }
    registry = FakeRegistry(
        manifest={
            "tools": [
                {"capability_id": "parse_ticket", "capability_version": "1.0.0"},
                {"capability_id": "tag_intent", "capability_version": "1.0.0"},
                {"capability_id": "draft_reply", "capability_version": "1.0.0"},
            ]
        }
    )
    tools = hydrate(
        {**START_BODY, "route_id": "ticket_triage"},
        catalogue,
        registry,
    )
    assert [tool["id"] for tool in tools] == [
        "parse_ticket",
        "tag_intent",
        "draft_reply",
        "respond",
    ]
    assert [tool["llm_role"] for tool in tools] == ["none", "none", "none", "synthesis"]

