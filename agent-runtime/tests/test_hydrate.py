import pytest

from app.agents.hydrate import HydrateError, hydrate
from tests.conftest import START_BODY, FakeCatalogue, FakeRegistry


def test_hydrate_fetches_manifest_and_each_capability() -> None:
    catalogue = FakeCatalogue()
    registry = FakeRegistry()
    tools = hydrate(START_BODY, catalogue, registry)
    assert catalogue.route_calls == [("fee_explain", "2026.08.1")]
    assert registry.manifest_calls == [("fee_explain_v1", "2026.08.1")]
    assert registry.capability_calls == [("account_fee_lookup", "1.0.0")]
    assert [tool["id"] for tool in tools] == ["account_fee_lookup"]
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
            "invoke": {"method": "POST", "url": "http://tool-mock:3010/notify"},
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
            "invoke": {"method": "POST", "url": "http://tool-mock:3010/clauses/search"},
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
