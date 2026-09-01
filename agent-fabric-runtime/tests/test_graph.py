from typing import Any

import pytest

from app.graph.customer_ask import CustomerAskWaiting
from app.graph.workflow import build_agent_loop, build_tool_graph
from tests.llm_fakes import TextLlm


def test_tool_graph_calls_each_hydrated_tool_in_order() -> None:
    calls: list[tuple[dict, dict]] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append((invoke, payload))
            return {"text": f"from-{invoke['url']}"}

    tools = [
        {
            "id": "account_fee_lookup",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/fees/explain"},
        },
        {
            "id": "list_accounts",
            "invoke": {"method": "GET", "url": "http://agent-mocks:3010/accounts"},
        },
    ]
    graph = build_tool_graph(tools, Invoker())
    output = graph.invoke({"result": "", "goal": {"utterance": "Why was I charged $42?"}})
    assert [invoke["url"] for invoke, _ in calls] == [
        "http://agent-mocks:3010/fees/explain",
        "http://agent-mocks:3010/accounts",
    ]
    assert calls[0][1] == {"utterance": "Why was I charged $42?"}
    assert calls[1][1] == {"utterance": "Why was I charged $42?"}
    assert output["result"] == "from-http://agent-mocks:3010/accounts"


def test_empty_manifest_completes_with_empty_result() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("no tools to call")

    graph = build_tool_graph([], Invoker())
    output = graph.invoke({"result": "", "goal": {}})
    assert output["result"] == ""


def test_query_formulation_asks_llm_then_calls_tool() -> None:
    calls: list[tuple[dict, dict]] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append((invoke, payload))
            return {"text": "clause 4.2"}

    class Llm:
        def complete(self, system: str, user: str) -> str:
            assert "Write the clause query" in system
            assert "clm-1001" in user
            return "exclusion 4.2 water damage"

    tools = [
        {
            "id": "clause_search",
            "llm_role": "query_formulation",
            "llm_prompt": "Write the clause query",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/legal/clauses/search"},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {"claim_id": "clm-1001"}})
    assert calls[0][1]["claim_id"] == "clm-1001"
    assert "notes" not in calls[0][1]
    assert calls[0][1]["query"] == "exclusion 4.2 water damage"
    assert output["result"] == "clause 4.2"


def test_synthesis_uses_llm_and_skips_tool() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("synthesis must not call the canned tool")

    class Llm:
        def complete(self, system: str, user: str) -> str:
            assert "Draft the memo" in system
            assert "clause 4.2" in user
            return "Deny: exclusion applies."

    tools = [
        {
            "id": "draft_memo",
            "llm_role": "synthesis",
            "llm_prompt": "Draft the memo",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/legal/memo"},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke(
        {"result": "", "goal": {"claim_id": "clm-1001"}, "notes": ["clause 4.2"]}
    )
    assert output["result"] == "Deny: exclusion applies."


def test_classify_passes_output_schema_to_llm() -> None:
    seen: list[object] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("classify must not call a tool")

    class Llm:
        def complete(self, system: str, user: str, schema: dict | None = None) -> str:
            seen.append(schema)
            return '{"merchant":"Acme","amount":45.36,"date":"2026-08-12"}'

    tools = [
        {
            "id": "extract_fields",
            "llm_role": "classify",
            "llm_prompt": "Return JSON only.",
            "output_schema": {
                "type": "object",
                "required": ["merchant", "amount", "date"],
                "properties": {
                    "merchant": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/unused"},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {"doc_id": "r-1"}})
    assert seen[0]["required"] == ["merchant", "amount", "date"]
    assert output["result"] == '{"merchant":"Acme","amount":45.36,"date":"2026-08-12"}'


def test_synthesis_passes_output_schema_to_llm() -> None:
    seen: list[object] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("synthesis must not call the canned tool")

    class Llm:
        def complete(self, system: str, user: str, schema: dict | None = None) -> str:
            seen.append(schema)
            return "Refund posted."

    tools = [
        {
            "id": "refund_confirm",
            "llm_role": "synthesis",
            "llm_prompt": "Write the confirm",
            "output_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {"text": {"type": "string"}},
            },
            "invoke": {},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {}, "notes": ["matched"]})
    assert seen[0]["required"] == ["text"]
    assert output["result"] == "Refund posted."


def test_query_formulation_passes_output_schema_to_llm() -> None:
    seen: list[object] = []
    calls: list[tuple[dict, dict]] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append((invoke, payload))
            return {"text": "clause 4.2"}

    class Llm:
        def complete(self, system: str, user: str, schema: dict | None = None) -> str:
            seen.append(schema)
            return "exclusion 4.2 water damage"

    tools = [
        {
            "id": "clause_search",
            "llm_role": "query_formulation",
            "llm_prompt": "Write the clause query",
            "output_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {"text": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/legal/clauses/search"},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {"claim_id": "clm-1001"}})
    assert seen[0]["required"] == ["text"]
    assert calls[0][1]["query"] == "exclusion 4.2 water damage"
    assert "notes" not in calls[0][1]
    assert output["result"] == "clause 4.2"


def test_http_after_classify_merges_slot_fields_not_notes() -> None:
    calls: list[dict] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(payload)
            return {"text": "matched"}

    class Llm:
        def complete(self, system: str, user: str, schema: dict | None = None) -> str:
            return '{"merchant":"Acme","amount":45.36,"date":"2026-08-12"}'

    tools = [
        {
            "id": "extract_fields",
            "llm_role": "classify",
            "llm_prompt": "Return JSON only.",
            "output_schema": {
                "type": "object",
                "required": ["merchant", "amount", "date"],
                "properties": {
                    "merchant": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                },
            },
            "invoke": {},
        },
        {
            "id": "match_purchase",
            "llm_role": "none",
            "input_schema": {
                "type": "object",
                "required": ["account_id", "merchant", "amount", "date"],
                "properties": {
                    "account_id": {"type": "string"},
                    "merchant": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/receipts/match"},
        },
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    graph.invoke({"result": "", "goal": {"doc_id": "r-1", "account_id": "a-1"}})
    assert calls == [
        {
            "account_id": "a-1",
            "merchant": "Acme",
            "amount": 45.36,
            "date": "2026-08-12",
        }
    ]


def test_http_after_classify_fails_when_slot_missing_required_fields() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("match must not run without classify fields")

    class Llm:
        def complete(self, system: str, user: str, schema: dict | None = None) -> str:
            return '{"merchant":"Acme"}'

    tools = [
        {
            "id": "extract_fields",
            "llm_role": "classify",
            "llm_prompt": "Return JSON only.",
            "invoke": {},
        },
        {
            "id": "match_purchase",
            "llm_role": "none",
            "input_schema": {
                "type": "object",
                "required": ["account_id", "merchant", "amount", "date"],
                "properties": {
                    "account_id": {"type": "string"},
                    "merchant": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/receipts/match"},
        },
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    try:
        graph.invoke({"result": "", "goal": {"account_id": "a-1"}})
    except RuntimeError as exc:
        assert "missing required field" in str(exc)
        return
    raise AssertionError("expected schema validation failure")


def test_http_merge_does_not_invent_fields_without_prior_slot() -> None:
    calls: list[dict] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(payload)
            return {"text": "first"}

    tools = [
        {
            "id": "identity_check",
            "llm_role": "none",
            "input_schema": {"type": "object", "required": ["customer_id"], "properties": {"customer_id": {"type": "string"}}},
            "output_schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}},
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/cards/identity"},
        },
        {
            "id": "match_purchase",
            "llm_role": "none",
            "input_schema": {
                "type": "object",
                "required": ["account_id", "merchant", "amount", "date"],
                "properties": {
                    "account_id": {"type": "string"},
                    "merchant": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/receipts/match"},
        },
    ]
    graph = build_tool_graph(tools, Invoker())
    try:
        graph.invoke({"result": "", "goal": {"customer_id": "c-1", "account_id": "a-1"}})
    except RuntimeError as exc:
        assert "missing required field" in str(exc)
        assert not calls or "merchant" not in (calls[-1] if calls else {})
        return
    raise AssertionError("expected missing merchant/amount/date")


def test_classify_slot_persisted_for_next_stage() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            return {"text": "matched"}

    class Llm:
        def complete(self, system: str, user: str, schema: dict | None = None) -> str:
            return '{"merchant":"Acme","amount":45.36,"date":"2026-08-12"}'

    tools = [
        {
            "id": "extract_fields",
            "llm_role": "classify",
            "llm_prompt": "Return JSON only.",
            "invoke": {},
        },
        {
            "id": "match_purchase",
            "llm_role": "none",
            "input_schema": {
                "type": "object",
                "required": ["account_id", "merchant", "amount", "date"],
                "properties": {
                    "account_id": {"type": "string"},
                    "merchant": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/receipts/match"},
        },
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {"account_id": "a-1"}, "slots": {}})
    assert output["slots"]["extract_fields"] == {
        "merchant": "Acme",
        "amount": 45.36,
        "date": "2026-08-12",
    }


def test_duplicate_charge_review_passes_customer_id_from_lookup_to_dup_check() -> None:
    """Pattern 2 seed: classify order_id → lookup → dup_check gets customer_id from lookup slot."""
    calls: list[dict] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(dict(payload))
            url = str(invoke.get("url") or "")
            if "lookup_order" in url:
                return {
                    "text": "Order ORD-77819 for Jane Doe.",
                    "order_id": "ORD-77819",
                    "customer_id": "CUS-1842",
                    "item_id": "jacket_blue_m",
                }
            return {
                "text": "No duplicate capture on ORD-77819.",
                "duplicate_charge_found": False,
            }

    class Llm:
        def complete(self, system: str, user: str, schema: dict | None = None) -> str:
            if schema and "order_id" in schema.get("properties", {}):
                return '{"order_id":"ORD-77819"}'
            return (
                "Order ORD-77819 was not double-charged; the second authorization is pending."
            )

    tools = [
        {
            "id": "duplicate_charge_intake",
            "llm_role": "classify",
            "llm_prompt": "Extract order_id from the goal utterance only.",
            "output_schema": {
                "type": "object",
                "required": ["order_id"],
                "properties": {"order_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/shopassist/intake"},
        },
        {
            "id": "lookup_order_by_order_id",
            "llm_role": "none",
            "input_schema": {
                "type": "object",
                "required": ["order_id"],
                "properties": {"order_id": {"type": "string"}},
            },
            "output_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string"},
                    "customer_id": {"type": "string", "x-agent-context": True},
                },
            },
            "invoke": {
                "method": "POST",
                "url": "http://agent-mocks:3010/shopassist/lookup_order",
            },
        },
        {
            "id": "investigate_duplicate_charge",
            "llm_role": "none",
            "input_schema": {
                "type": "object",
                "required": ["order_id", "customer_id"],
                "properties": {
                    "order_id": {"type": "string"},
                    "customer_id": {"type": "string"},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string"},
                    "duplicate_charge_found": {"type": "boolean", "x-agent-context": True},
                },
            },
            "invoke": {
                "method": "POST",
                "url": "http://agent-mocks:3010/shopassist/investigate_duplicate_charge",
            },
        },
        {
            "id": "duplicate_charge_respond",
            "llm_role": "synthesis",
            "llm_prompt": "Write the customer reply from prior stage outputs only.",
            "invoke": {},
        },
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    goal = {"utterance": "I was charged twice on order ORD-77819"}
    output = graph.invoke({"result": "", "goal": goal, "slots": {}})
    assert calls == [
        {"order_id": "ORD-77819"},
        {"order_id": "ORD-77819", "customer_id": "CUS-1842"},
    ]
    assert output["slots"]["duplicate_charge_intake"] == {"order_id": "ORD-77819"}
    assert "not double-charged" in output["result"]


def test_ticket_triage_passes_parse_fields_to_tag_intent() -> None:
    """Pattern 3 seed: parse_ticket slot → tag_intent HTTP body (guided outer walk)."""
    calls: list[dict] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(dict(payload))
            url = str(invoke.get("url") or "")
            if "parse_ticket" in url:
                return {
                    "text": "Parsed billing inquiry.",
                    "category": "billing",
                    "order_ref": "ORD-77819",
                    "customer_email": "jane.doe@shopassist.example",
                }
            return {
                "text": "Intent tagged.",
                "intent": "duplicate_charge",
                "priority": "normal",
            }

    class FakeJobs:
        def start(self, *_args, **_kwargs) -> dict[str, Any]:
            raise AssertionError("child agent runs after tag_intent in a separate test")

    tools = [
        {
            "id": "parse_ticket",
            "llm_role": "none",
            "input_schema": {
                "type": "object",
                "properties": {"utterance": {"type": "string"}},
            },
            "output_schema": {
                "type": "object",
                "required": ["text", "category", "order_ref"],
                "properties": {
                    "text": {"type": "string"},
                    "category": {"type": "string"},
                    "order_ref": {"type": "string"},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/support/parse_ticket"},
        },
        {
            "id": "tag_intent",
            "llm_role": "none",
            "input_schema": {
                "type": "object",
                "required": ["category", "order_ref"],
                "properties": {
                    "category": {"type": "string"},
                    "order_ref": {"type": "string"},
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["text", "intent", "priority"],
                "properties": {
                    "text": {"type": "string"},
                    "intent": {"type": "string", "x-agent-context": True},
                    "priority": {"type": "string", "x-agent-context": True},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/support/tag_intent"},
        },
    ]
    graph = build_tool_graph(tools, Invoker(), jobs=FakeJobs())
    output = graph.invoke(
        {
            "result": "",
            "goal": {"utterance": "Customer charged twice on ORD-77819"},
            "slots": {},
        }
    )
    assert calls[1] == {"category": "billing", "order_ref": "ORD-77819"}
    assert output["slots"]["parse_ticket"]["order_ref"] == "ORD-77819"


def test_ticket_triage_starts_draft_reply_child_with_projected_payload() -> None:
    """Pattern 3 reply stage: kind=agent posts ticket_draft_reply child job with join."""
    from app.graph.subagent_gate import SubagentWaiting

    calls: list[tuple[str, str, dict[str, Any]]] = []

    class FakeJobs:
        def start(
            self,
            route_id: str,
            idempotency_key: str,
            payload: dict[str, Any],
            *,
            invoke: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            calls.append((route_id, idempotency_key, payload))
            return {"correlation_id": "corr-child-draft-1"}

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("draft_reply is kind=agent, not domain HTTP")

    graph = build_tool_graph(
        [
            {
                "id": "draft_reply",
                "kind": "agent",
                "llm_role": "none",
                "input_schema": {
                    "type": "object",
                    "required": [
                        "utterance",
                        "category",
                        "order_ref",
                        "intent",
                        "priority",
                    ],
                    "properties": {
                        "utterance": {"type": "string"},
                        "category": {"type": "string"},
                        "order_ref": {"type": "string"},
                        "intent": {"type": "string"},
                        "priority": {"type": "string"},
                    },
                },
                "invoke": {
                    "method": "POST",
                    "url": "https://api-afd.internal/v1/jobs",
                    "join": True,
                    "body": {"route_id": "ticket_draft_reply"},
                },
            }
        ],
        Invoker(),
        jobs=FakeJobs(),
    )
    try:
        graph.invoke(
            {
                "result": "",
                "goal": {"utterance": "Customer charged twice on ORD-77819"},
                "notes": ["parse_ticket: category=billing, order_ref=ORD-77819", "tag_intent: intent=duplicate_charge, priority=normal"],
                "slots": {
                    "parse_ticket": {
                        "category": "billing",
                        "order_ref": "ORD-77819",
                    },
                    "tag_intent": {
                        "intent": "duplicate_charge",
                        "priority": "normal",
                    },
                },
                "correlation_id": "corr-parent-triage-1",
            }
        )
    except SubagentWaiting as exc:
        assert calls == [
            (
                "ticket_draft_reply",
                "subagent-corr-parent-triage-1-draft_reply",
                {
                    "utterance": "Customer charged twice on ORD-77819",
                    "category": "billing",
                    "order_ref": "ORD-77819",
                    "intent": "duplicate_charge",
                    "priority": "normal",
                },
            )
        ]
        assert exc.stage_id == "draft_reply"
        return
    raise AssertionError("expected subagent join waiting after kind=agent start")


def test_classify_uses_llm_and_skips_tool() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("classify must not call a tool")

    class Llm:
        def complete(self, system: str, user: str) -> str:
            assert "Extract the requested fields" in system
            return '{"claim_type":"water"}'

    tools = [
        {
            "id": "extract",
            "llm_role": "classify",
            "llm_prompt": "Extract the requested fields from the input only.",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/unused"},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {"claim_id": "clm-1001"}})
    assert output["result"] == '{"claim_type":"water"}'


def test_none_role_calls_tool_without_llm() -> None:
    calls: list[dict] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(payload)
            return {"text": "playbook hit"}

    class Llm:
        def complete(self, system: str, user: str) -> str:
            raise AssertionError("none must not call the LLM")

    tools = [
        {
            "id": "policy_search",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/legal/playbook/search"},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {"claim_id": "clm-1001"}})
    assert calls == [{"claim_id": "clm-1001"}]
    assert output["result"] == "playbook hit"


def test_unknown_llm_role_fails() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("unknown role must not call a tool")

    class Llm:
        def complete(self, system: str, user: str) -> str:
            raise AssertionError("unknown role must not call the LLM")

    graph = build_tool_graph(
        [{"id": "x", "llm_role": "rewrite", "invoke": {"method": "POST", "url": "http://x"}}],
        Invoker(),
        llm=Llm(),
    )
    try:
        graph.invoke({"result": "", "goal": {}})
    except RuntimeError as exc:
        assert "unknown llm_role" in str(exc)
        return
    raise AssertionError("expected unknown llm_role")


def test_none_without_url_is_noop() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("prefetch must not call HTTP without a url")

    class Llm:
        def complete(self, system: str, user: str) -> str:
            raise AssertionError("none must not call the LLM")

    graph = build_tool_graph(
        [{"id": "prefetch", "llm_role": "none", "invoke": {}}],
        Invoker(),
        llm=Llm(),
    )
    output = graph.invoke({"result": "", "goal": {"claim_id": "clm-1001"}, "notes": ["packed"]})
    assert output["result"] == "packed"
    assert output["notes"] == ["packed"]


def test_prefetch_stage_packs_scope_into_slot_and_notes() -> None:
    from tests.conftest import FakeCatalogue
    from tests.test_prefetch import FakePrefetch

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("prefetch stage must not call domain tools")

    class Llm:
        last_user = ""

        def complete(self, system: str, user: str, schema=None) -> str:
            Llm.last_user = user
            return "Memo from pack."

    catalogue = FakeCatalogue()
    catalogue.corpora = {
        "policy-engine": {
            "corpus_id": "policy-engine",
            "url": "http://agent-mocks:3010/v1/search/assistant",
            "collection": "policy-engine",
            "status": "published",
        }
    }
    prefetch = FakePrefetch()
    tools = [
        {"id": "prefetch", "llm_role": "none", "invoke": {}},
        {"id": "generate", "llm_role": "synthesis", "llm_prompt": "Draft memo", "invoke": {}},
    ]
    graph = build_tool_graph(
        tools,
        Invoker(),
        llm=Llm(),
        retrieval={"mode": "deterministic_prefetch", "scope": ["policy-engine"]},
        prefetch=prefetch,
        catalogue=catalogue,
    )
    output = graph.invoke({"result": "", "goal": {"topic": "refunds"}})
    assert prefetch.calls
    assert "policy-engine" in output["slots"]["prefetch"]["chunks"][0]["corpus_id"]
    assert "[policy-engine:" in output["notes"][0]
    assert output["result"] == "Memo from pack."
    assert "packed chunks:" in Llm.last_user
    assert "Refund window" in Llm.last_user
    assert "prefetch:policy-engine" in output["slots"]
    assert output["slots"]["prefetch:policy-engine"]["corpus_id"] == "policy-engine"


def test_prefetch_on_stage_emits_per_corpus() -> None:
    from tests.conftest import FakeCatalogue
    from tests.test_prefetch import FakePrefetch

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("prefetch stage must not call domain tools")

    class Llm:
        def complete(self, system: str, user: str, schema=None) -> str:
            return "ok"

    catalogue = FakeCatalogue()
    catalogue.corpora = {
        "fee-schedule": {
            "corpus_id": "fee-schedule",
            "url": "http://mocks/fee",
            "collection": "fee-schedule",
            "status": "published",
        },
        "product-disclosure": {
            "corpus_id": "product-disclosure",
            "url": "http://mocks/pds",
            "collection": "product-disclosure",
            "status": "published",
        },
    }
    seen: list[str] = []

    def on_stage(step: int, stage_id: str, state: dict) -> None:
        seen.append(stage_id)

    graph = build_tool_graph(
        [
            {"id": "prefetch", "llm_role": "none", "invoke": {}},
            {"id": "generate", "llm_role": "synthesis", "llm_prompt": "Answer", "invoke": {}},
        ],
        Invoker(),
        llm=Llm(),
        retrieval={
            "mode": "deterministic_prefetch",
            "scope": ["fee-schedule", "product-disclosure"],
        },
        prefetch=FakePrefetch(),
        catalogue=catalogue,
        on_stage=on_stage,
    )
    graph.invoke({"result": "", "goal": {"q": "fee"}})
    assert seen == ["prefetch:fee-schedule", "prefetch:product-disclosure", "generate"]


def test_prefetch_route_synthesis_fails_when_pack_missing() -> None:
    from tests.conftest import FakeCatalogue
    from tests.test_prefetch import FakePrefetch

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("synthesis must not call HTTP")

    class Llm:
        def complete(self, system: str, user: str, schema=None) -> str:
            raise AssertionError("synthesis must not run without prefetch pack")

    catalogue = FakeCatalogue()
    catalogue.corpora = {
        "policy-engine": {
            "corpus_id": "policy-engine",
            "url": "http://agent-mocks:3010/v1/search/assistant",
            "collection": "policy-engine",
            "status": "published",
        }
    }
    tools = [
        {"id": "prefetch", "llm_role": "none", "invoke": {}},
        {"id": "generate", "llm_role": "synthesis", "llm_prompt": "Draft memo", "invoke": {}},
    ]
    graph = build_tool_graph(
        tools,
        Invoker(),
        llm=Llm(),
        retrieval={"mode": "deterministic_prefetch", "scope": ["policy-engine"]},
        prefetch=FakePrefetch(chunks=[]),
        catalogue=catalogue,
    )
    try:
        graph.invoke({"result": "", "goal": {"topic": "refunds"}})
    except RuntimeError as exc:
        assert "no chunks" in str(exc) or "prefetch slot is empty" in str(exc)
        return
    raise AssertionError("expected prefetch pack failure")


def test_prefetch_stage_fails_when_gateway_returns_no_chunks() -> None:
    from tests.conftest import FakeCatalogue
    from tests.test_prefetch import FakePrefetch

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("prefetch stage must not call domain tools")

    catalogue = FakeCatalogue()
    catalogue.corpora = {
        "policy-engine": {
            "corpus_id": "policy-engine",
            "url": "http://agent-mocks:3010/v1/search/assistant",
            "collection": "policy-engine",
            "status": "published",
        }
    }
    graph = build_tool_graph(
        [{"id": "prefetch", "llm_role": "none", "invoke": {}}],
        Invoker(),
        retrieval={"mode": "deterministic_prefetch", "scope": ["policy-engine"]},
        prefetch=FakePrefetch(chunks=[]),
        catalogue=catalogue,
    )
    try:
        graph.invoke({"result": "", "goal": {}})
    except RuntimeError as exc:
        assert "no chunks" in str(exc)
        return
    raise AssertionError("expected prefetch failure")


def _kyc_branch_tools() -> list[dict]:
    return [
        {
            "id": "kyc_risk_engine",
            "workflow_stage_id": "risk_score",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/kyc/risk"},
            "branch": {"high": "manual_review", "low": "activate_account"},
        },
        {
            "id": "manual_review",
            "workflow_stage_id": "manual_review",
            "stage_type": "human_gate",
            "llm_role": "none",
            "invoke": {},
        },
        {
            "id": "account_activate",
            "workflow_stage_id": "activate_account",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/kyc/activate"},
        },
        {
            "id": "summarize",
            "workflow_stage_id": "summarize",
            "llm_role": "synthesis",
            "llm_prompt": "Summarize KYC",
            "invoke": {},
        },
    ]


def test_branch_low_routes_to_activate_not_manual_review() -> None:
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(str(invoke.get("url") or ""))
            if invoke["url"].endswith("/kyc/risk"):
                return {"risk": "low", "text": "KYC risk: low."}
            return {"text": "activated"}

    class Llm:
        def complete(self, system: str, user: str, schema=None) -> str:
            return "KYC summary."

    graph = build_tool_graph(_kyc_branch_tools(), Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {"applicant_id": "app-1"}})
    assert calls == [
        "http://agent-mocks:3010/kyc/risk",
        "http://agent-mocks:3010/kyc/activate",
    ]
    assert output["result"] == "KYC summary."


def test_branch_high_routes_to_manual_review_not_activate() -> None:
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(str(invoke.get("url") or ""))
            return {"risk": "high", "text": "KYC risk: high."}

    class Llm:
        def complete(self, system: str, user: str, schema=None) -> str:
            raise AssertionError("synthesis must not run before human_gate resume")

    from app.graph.human_gate import HumanGateWaiting

    graph = build_tool_graph(_kyc_branch_tools(), Invoker(), llm=Llm())
    try:
        graph.invoke({"result": "", "goal": {"applicant_id": "app-2"}})
    except HumanGateWaiting as exc:
        assert calls == ["http://agent-mocks:3010/kyc/risk"]
        assert exc.stage_id == "manual_review"
        assert exc.resume_index == 3
        return
    raise AssertionError("expected human_gate waiting")


def test_human_gate_resume_runs_merge_stage_only() -> None:
    from app.graph.human_gate import resume_index_after_gate

    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(str(invoke.get("url") or ""))
            return {"risk": "high", "text": "KYC risk: high."}

    class Llm:
        def complete(self, system: str, user: str, schema=None) -> str:
            return "KYC summary."

    tools = _kyc_branch_tools()
    graph = build_tool_graph(
        tools,
        Invoker(),
        llm=Llm(),
        start_index=resume_index_after_gate(tools, 1),
    )
    output = graph.invoke(
        {
            "result": "",
            "goal": {"applicant_id": "app-2"},
            "slots": {"manual_review": {"decision": "approve", "reviewer_id": "ops-1"}},
        }
    )
    assert calls == []
    assert output["result"] == "KYC summary."


def test_branch_unknown_risk_fails_closed() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            return {"risk": "medium", "text": "KYC risk: medium."}

    graph = build_tool_graph(_kyc_branch_tools(), Invoker(), llm=object())
    try:
        graph.invoke({"result": "", "goal": {"applicant_id": "app-3"}})
    except RuntimeError as exc:
        assert "no known key" in str(exc)
        return
    raise AssertionError("expected branch routing failure")


def test_agent_kind_posts_projected_child_goal() -> None:
    calls: list[tuple[str, str, dict[str, Any], dict[str, Any] | None]] = []

    class FakeJobs:
        def start(
            self,
            route_id: str,
            idempotency_key: str,
            payload: dict[str, Any],
            *,
            invoke: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            calls.append((route_id, idempotency_key, payload, invoke))
            return {"correlation_id": "corr-child-1"}

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("kind=agent must POST jobs, not domain HTTP")

    graph = build_tool_graph(
        [
            {
                "id": "start_contract_review",
                "kind": "agent",
                "input_schema": {
                    "type": "object",
                    "required": ["document_id"],
                    "properties": {
                        "document_id": {"type": "string"},
                        "matter_id": {"type": "string"},
                    },
                },
                "invoke": {
                    "method": "POST",
                    "url": "https://api-afd.internal/v1/jobs",
                    "body": {"route_id": "contract_review"},
                },
            }
        ],
        Invoker(),
        jobs=FakeJobs(),
    )
    output = graph.invoke(
        {
            "result": "",
            "goal": {"document_id": "doc-1", "noise": "drop-me"},
            "notes": ["prior prose must not leak"],
            "slots": {"ocr_extract": {"matter_id": "m-9"}},
            "correlation_id": "corr-parent-1",
        }
    )
    assert calls == [
        (
            "contract_review",
            "subagent-corr-parent-1-start_contract_review",
            {"document_id": "doc-1", "matter_id": "m-9"},
            {
                "method": "POST",
                "url": "https://api-afd.internal/v1/jobs",
                "body": {"route_id": "contract_review"},
            },
        )
    ]
    assert "noise" not in calls[0][2]
    assert "Started subagent contract_review" in output["result"]
    assert output["slots"]["start_contract_review"]["payload"] == {
        "document_id": "doc-1",
        "matter_id": "m-9",
    }


def test_agent_kind_fails_closed_when_required_child_field_missing() -> None:
    class FakeJobs:
        def start(self, *_args, **_kwargs) -> dict[str, Any]:
            raise AssertionError("jobs must not start when projection is incomplete")

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            return {"text": "ok"}

    graph = build_tool_graph(
        [
            {
                "id": "start_kyc_onboarding",
                "kind": "agent",
                "input_schema": {
                    "type": "object",
                    "required": ["applicant_id"],
                    "properties": {
                        "applicant_id": {"type": "string"},
                        "ticket_id": {"type": "string"},
                    },
                },
                "invoke": {
                    "method": "POST",
                    "url": "https://api-afd.internal/v1/jobs",
                    "body": {"route_id": "kyc_onboarding"},
                },
            }
        ],
        Invoker(),
        jobs=FakeJobs(),
    )
    try:
        graph.invoke(
            {
                "result": "",
                "goal": {"ticket_id": "t-1"},
                "notes": ["do not pass notes to child"],
                "slots": {},
                "correlation_id": "corr-parent-2",
            }
        )
    except RuntimeError as exc:
        assert "applicant_id" in str(exc)
        return
    raise AssertionError("expected missing child field failure")


def test_classify_without_llm_raises() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("classify must not fall back to HTTP")

    graph = build_tool_graph(
        [{"id": "extract", "llm_role": "classify", "llm_prompt": "Extract", "invoke": {}}],
        Invoker(),
    )
    try:
        graph.invoke({"result": "", "goal": {}})
    except RuntimeError as exc:
        assert "llm required" in str(exc)
        return
    raise AssertionError("expected llm required")


def test_on_stage_fires_after_each_tool() -> None:
    seen: list[tuple[int, str, str]] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            return {"text": f"from-{invoke['url']}"}

    def on_stage(step: int, stage_id: str, state: dict) -> None:
        seen.append((step, stage_id, str(state.get("result") or "")))

    tools = [
        {"id": "a", "invoke": {"method": "POST", "url": "http://x/a"}},
        {"id": "b", "invoke": {"method": "POST", "url": "http://x/b"}},
    ]
    graph = build_tool_graph(tools, Invoker(), on_stage=on_stage)
    graph.invoke({"result": "", "goal": {}})
    assert seen == [(0, "a", "from-http://x/a"), (1, "b", "from-http://x/b")]


def test_agent_loop_calls_tool_then_done() -> None:
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {"text": "Fee of $42 is the monthly account charge."}

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if self.turns == 1:
                assert "account_fee_lookup" in system
                return "CALL account_fee_lookup"
            assert "Fee of $42" in user
            return "DONE Fee of $42 is the monthly account charge."

    tools = [
        {
            "id": "account_fee_lookup",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/fees/explain"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm())
    output = graph.invoke({"result": "", "goal": {"utterance": "Why $42?"}, "notes": []})
    assert calls == ["http://agent-mocks:3010/fees/explain"]
    assert output["result"] == "Fee of $42 is the monthly account charge."


def test_agent_loop_tool_call_message_emits_on_progress() -> None:
    from app.graph.agent_loop.decision import AgentDecision

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            return {"order_id": "ORD-77819", "text": "Order found."}

    class Llm:
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str, schema=None) -> str:
            raise AssertionError("structured only")

        def complete_structured(self, system: str, user: str, schema) -> AgentDecision:
            self.turns += 1
            if self.turns == 1:
                return AgentDecision(
                    action="tool_call",
                    tool_name="lookup_order_by_order_id",
                    arguments={"order_id": "ORD-77819"},
                    message="Thank you. Let me look up your order ORD-77819 right away.",
                )
            return AgentDecision(action="done", message="Order ORD-77819 found.")

    progress: list[str] = []

    def on_progress(message: str) -> None:
        progress.append(message)

    tools = [
        {
            "id": "lookup_order_by_order_id",
            "input_schema": {
                "type": "object",
                "required": ["order_id"],
                "properties": {"order_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/lookup_order"},
        }
    ]
    graph = build_agent_loop(
        tools,
        Invoker(),
        Llm(),
        max_steps=4,
        on_progress=on_progress,
    )
    output = graph.invoke(
        {
            "result": "",
            "goal": {"utterance": "lookup ORD-77819"},
            "notes": ["customer: ORD-77819"],
        }
    )
    assert progress == ["Thank you. Let me look up your order ORD-77819 right away."]
    assert output["result"]


def test_agent_loop_skips_repeat_lookup_without_second_http_call() -> None:
    """Repeat lookup tool_call does not POST again when the slot already exists."""
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {
                "order_id": "ORD-77819",
                "item_id": "jacket_blue_m",
                "text": "Order ORD-77819: Blue Jacket $149.",
            }

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if self.turns <= 2:
                return 'CALL lookup_order_by_order_id\n{"order_id":"ORD-77819"}'
            return "DONE Order found."

    tools = [
        {
            "id": "lookup_order_by_order_id",
            "input_schema": {
                "type": "object",
                "required": ["order_id"],
                "properties": {"order_id": {"type": "string"}},
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "order_id": {"type": "string", "x-agent-context": True},
                    "item_id": {"type": "string", "x-agent-context": True},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/shopassist/lookup_order"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=6)
    output = graph.invoke(
        {
            "result": "",
            "goal": {"utterance": "damaged jacket ORD-77819"},
            "notes": ["customer: ORD-77819"],
        }
    )
    assert calls == ["http://agent-mocks:3010/shopassist/lookup_order"]
    assert any("already completed" in note for note in output["notes"])
    assert sum(1 for note in output["notes"] if note.startswith("lookup_order_by_order_id:")) == 2


def test_agent_loop_escalate_auto_completes_without_further_llm_turns() -> None:
    """After escalate_to_human succeeds, the parent run ends without another LLM turn."""
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {"handoff_id": "hof-1", "text": "Handoff opened: hof-1."}

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if self.turns == 1:
                return 'CALL escalate_to_human\n{"order_id":"ORD-1"}'
            raise AssertionError("LLM should not run again after handoff auto-complete")

    tools = [
        {
            "id": "escalate_to_human",
            "output_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string"},
                    "handoff_id": {"type": "string", "x-agent-context": True},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/handoff/escalate"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=6)
    output = graph.invoke({"result": "", "goal": {"utterance": "need help"}, "notes": []})
    assert calls == ["http://agent-mocks:3010/handoff/escalate"]
    assert "hof-1" in output["result"]


def test_agent_loop_escalate_idempotent_skips_second_post() -> None:
    """Re-CALL escalate_to_human after success does not POST again and completes the run."""
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {"handoff_id": "hof-99", "text": "Handoff opened: hof-99."}

    class Llm(TextLlm):
        def complete(self, system: str, user: str) -> str:
            return 'CALL escalate_to_human\n{"order_id":"ORD-1"}'

    tools = [
        {
            "id": "escalate_to_human",
            "output_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string"},
                    "handoff_id": {"type": "string", "x-agent-context": True},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/handoff/escalate"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    output = graph.invoke(
        {
            "result": "",
            "goal": {"utterance": "need help"},
            "notes": [],
            "slots": {"escalate_to_human": {"handoff_id": "hof-1", "text": "Handoff opened: hof-1."}},
        }
    )
    assert calls == []
    assert "hof-1" in output["result"]


def test_agent_loop_handoff_then_done() -> None:
    """Successful handoff auto-completes the parent without a second LLM turn."""
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {"handoff_id": "hof-1", "text": "Handoff opened: hof-1."}

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if self.turns == 1:
                return "CALL open_handoff"
            raise AssertionError("handoff should auto-complete without another LLM turn")

    tools = [
        {
            "id": "open_handoff",
            "output_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {"text": {"type": "string"}, "handoff_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/handoff/open"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    output = graph.invoke({"result": "", "goal": {"utterance": "need help"}, "notes": []})
    assert calls == ["http://agent-mocks:3010/handoff/open"]
    assert "hof-1" in output["result"]
    assert (output.get("slots") or {}).get("open_handoff", {}).get("handoff_id") == "hof-1"


def test_agent_loop_handoff_with_subagent_pending() -> None:
    """Handoff can run while a child join is still pending; LLM closes with DONE."""
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {"handoff_id": "hof-2", "text": "Handoff opened: hof-2."}

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if self.turns == 1:
                return "CALL open_handoff"
            return "DONE waiting on subagent then closing"

    tools = [
        {
            "id": "open_handoff",
            "output_schema": {
                "type": "object",
                "required": ["text"],
                "properties": {"text": {"type": "string"}, "handoff_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/handoff/open"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    output = graph.invoke(
        {
            "result": "",
            "goal": {"utterance": "need help"},
            "notes": [],
            "slots": {
                "start_contract_review": {
                    "correlation_id": "corr-pending-1",
                    "route_id": "contract_review",
                    "status": "running",
                }
            },
        }
    )
    assert calls == ["http://agent-mocks:3010/handoff/open"]
    assert output["result"] == "waiting on subagent then closing"


def test_agent_loop_tool_schema_miss_observes_and_continues() -> None:
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {"text": "should-not-run"}

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if self.turns == 1:
                return "CALL account_fee_lookup"
            assert "tool error" in user and "account_id" in user
            return "DONE Fee of $42 is the monthly account charge."

    tools = [
        {
            "id": "account_fee_lookup",
            "input_schema": {
                "type": "object",
                "required": ["account_id"],
                "properties": {"account_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/fees/explain"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    output = graph.invoke({"result": "", "goal": {"utterance": "Why was I charged $42?"}, "notes": []})
    assert calls == []
    assert output["result"] == "Fee of $42 is the monthly account charge."


def test_agent_loop_preflight_rejects_ungrounded_order_id() -> None:
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {"text": "should-not-run"}

    class Llm(TextLlm):
        def complete(self, system: str, user: str) -> str:
            return 'CALL lookup_order_by_order_id\n{"order_id":"ORD-99999"}'

    tools = [
        {
            "id": "lookup_order_by_order_id",
            "input_schema": {
                "type": "object",
                "required": ["order_id"],
                "properties": {
                    "order_id": {
                        "type": "string",
                        "pattern": "^ORD-\\d+$",
                        "x-ground-in-user-context": True,
                    }
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/shopassist/lookup_order"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    with pytest.raises(CustomerAskWaiting):
        graph.invoke({"result": "", "goal": {"utterance": "jacket damaged"}, "notes": []})
    assert calls == []


def test_agent_loop_preflight_rejects_placeholder_order_id() -> None:
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(invoke["url"])
            return {"text": "should-not-run"}

    class Llm(TextLlm):
        def complete(self, system: str, user: str) -> str:
            return 'CALL lookup_order_by_order_id\n{"order_id":"ask"}'

    tools = [
        {
            "id": "lookup_order_by_order_id",
            "input_schema": {
                "type": "object",
                "required": ["order_id"],
                "properties": {
                    "order_id": {
                        "type": "string",
                        "pattern": "^ORD-\\d+$",
                        "x-ground-in-user-context": True,
                    }
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/shopassist/lookup_order"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    with pytest.raises(CustomerAskWaiting) as exc_info:
        graph.invoke({"result": "", "goal": {"utterance": "jacket damaged"}, "notes": []})
    assert calls == []
    assert "order number" in exc_info.value.message.lower()


def test_agent_loop_keeps_waiting_after_ask_without_customer_reply() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("must not invoke tools while waiting for customer reply")

    class Llm(TextLlm):
        def complete(self, system: str, user: str) -> str:
            raise AssertionError("must not call LLM while waiting for customer reply")

    tools = [
        {
            "id": "lookup_order_by_order_id",
            "input_schema": {
                "type": "object",
                "required": ["order_id"],
                "properties": {
                    "order_id": {
                        "type": "string",
                        "pattern": "^ORD-\\d+$",
                        "x-ground-in-user-context": True,
                    }
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/shopassist/lookup_order"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    ask = "What is your order number? It should look like ORD-77819."
    with pytest.raises(CustomerAskWaiting) as exc_info:
        graph.invoke(
            {
                "result": ask,
                "goal": {"utterance": "jacket damaged"},
                "notes": [f"ask: {ask}"],
            }
        )
    assert exc_info.value.message == ask


def test_agent_loop_call_args_are_schema_only() -> None:
    seen: list[dict] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            seen.append(payload)
            return {"text": "Record REC-77819: widget."}

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if self.turns == 1:
                return 'CALL fetch_record\n{"record_id":"REC-77819"}'
            return "DONE Record REC-77819: widget."

    tools = [
        {
            "id": "fetch_record",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {"record_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/fetch"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm())
    output = graph.invoke(
        {"result": "", "goal": {"utterance": "need help"}, "notes": []}
    )
    assert seen == [{"record_id": "REC-77819"}]
    assert "REC-77819" in output["result"]


def test_agent_loop_calls_fetch_with_llm_json_after_customer_note() -> None:
    seen: list[dict] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            seen.append(payload)
            return {"text": "Record REC-77819: widget $149."}

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if "Record REC-77819" in user:
                return "DONE Record REC-77819: widget $149."
            if "customer: REC-77819" in user:
                return 'CALL fetch_record\n{"record_id":"REC-77819"}'
            return "CALL fetch_record"

    tools = [
        {
            "id": "fetch_record",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {"record_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/fetch"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    output = graph.invoke(
        {
            "result": "",
            "goal": {"utterance": "need help"},
            "notes": [
                "Please provide a record id.",
                "customer: REC-77819",
            ],
            "_resume_loop_step": 1,
        }
    )
    assert seen == [{"record_id": "REC-77819"}]
    assert "REC-77819" in output["result"]


def test_agent_loop_ask_raises_customer_ask_waiting() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("ASK must not invoke tools")

    class Llm(TextLlm):
        def complete(self, system: str, user: str) -> str:
            return "ASK Please provide a record id."

    tools = [
        {
            "id": "fetch_record",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/fetch"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm())
    try:
        graph.invoke({"result": "", "goal": {"utterance": "need help"}, "notes": []})
    except CustomerAskWaiting as exc:
        assert "record id" in exc.message
        assert exc.state.get("result")
        return
    raise AssertionError("expected CustomerAskWaiting")


def test_agent_loop_uses_llm_call_after_customer_note() -> None:
    seen: list[dict] = []
    llm_calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            seen.append(payload)
            return {"text": "Record REC-55210: item $89."}

    class Llm(TextLlm):
        def complete(self, system: str, user: str) -> str:
            llm_calls.append(user)
            if "Record REC-55210" in user:
                return "DONE Record REC-55210: item $89."
            if "customer: REC-55210" in user:
                return 'CALL fetch_record\n{"record_id":"REC-55210"}'
            return "ASK Please provide a record id."

    tools = [
        {
            "id": "fetch_record",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {"record_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/fetch"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=4)
    output = graph.invoke(
        {
            "result": "",
            "goal": {"utterance": "missing item"},
            "notes": [
                "Please provide a record id.",
                "customer: REC-55210",
            ],
            "_resume_loop_step": 1,
        }
    )
    assert seen == [{"record_id": "REC-55210"}]
    assert any("customer: REC-55210" in call for call in llm_calls)
    assert "REC-55210" in output["result"]


def test_agent_loop_multi_tool_flow_completes() -> None:
    """Scripted LLM walks fetch → billing → policy → handoff."""
    seen: list[tuple[str, dict]] = []
    stages: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            seen.append((invoke["url"], payload))
            url = invoke["url"]
            if url.endswith("/tools/fetch"):
                return {
                    "record_id": "REC-77819",
                    "item_id": "item_blue_m",
                    "price": 149.0,
                    "text": "Record REC-77819: widget $149.",
                }
            if url.endswith("/tools/check_billing"):
                return {"duplicate_found": False, "text": "No duplicate capture on REC-77819."}
            if url.endswith("/tools/check_policy"):
                return {
                    "eligible": True,
                    "automatic_limit": 75.0,
                    "text": "Policy v7: eligible; $149 requires human review.",
                }
            if url.endswith("/handoff/open"):
                return {"handoff_id": "hof-1", "text": "Handoff opened: hof-1."}
            raise AssertionError(url)

    class Llm(TextLlm):
        def complete(self, system: str, user: str) -> str:
            if "Record REC-77819" not in user:
                return 'CALL fetch_record\n{"record_id":"REC-77819"}'
            if "No duplicate capture" not in user and "duplicate_found" not in user:
                return 'CALL check_billing\n{"record_id":"REC-77819"}'
            if "Policy v7" not in user:
                return (
                    'CALL check_policy\n'
                    '{"record_id":"REC-77819","item_id":"item_blue_m","reason":"damaged"}'
                )
            if "Handoff opened" not in user:
                return (
                    'CALL open_handoff\n'
                    '{"record_id":"REC-77819","reason":"above automatic limit"}'
                )
            return "DONE Handoff opened: hof-1."

    tools = [
        {
            "id": "fetch_record",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {"record_id": {"type": "string"}},
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "record_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "price": {"type": "number"},
                    "text": {"type": "string"},
                },
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/fetch"},
        },
        {
            "id": "check_billing",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {"record_id": {"type": "string"}},
            },
            "output_schema": {"type": "object"},
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/check_billing"},
        },
        {
            "id": "check_policy",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {
                    "record_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
            "output_schema": {"type": "object"},
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/check_policy"},
        },
        {
            "id": "open_handoff",
            "output_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "handoff_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/handoff/open"},
        },
    ]

    def on_stage(step: int, stage_id: str, state: dict) -> None:
        stages.append(stage_id)

    graph = build_agent_loop(tools, Invoker(), Llm(), max_steps=12, on_stage=on_stage)
    output = graph.invoke(
        {
            "result": "",
            "goal": {"utterance": "damaged widget, charged twice, full refund"},
            "notes": [
                "Please provide a record id.",
                "customer: REC-77819",
            ],
            "_resume_loop_step": 1,
        }
    )
    assert [url for url, _ in seen] == [
        "http://agent-mocks:3010/tools/fetch",
        "http://agent-mocks:3010/tools/check_billing",
        "http://agent-mocks:3010/tools/check_policy",
        "http://agent-mocks:3010/handoff/open",
    ]
    assert "hof-1" in output["result"]
    assert stages[-1] == "respond"
    assert any("hof-1" in note for note in output["notes"])
    assert any("Policy v7" in note for note in output["notes"])
