from app.graph.workflow import build_agent_loop, build_tool_graph


def test_tool_graph_calls_each_hydrated_tool_in_order() -> None:
    calls: list[tuple[dict, dict]] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append((invoke, payload))
            return {"text": f"from-{invoke['url']}"}

    tools = [
        {
            "id": "account_fee_lookup",
            "invoke": {"method": "POST", "url": "http://tool-mock:3010/fees/explain"},
        },
        {
            "id": "list_accounts",
            "invoke": {"method": "GET", "url": "http://tool-mock:3010/accounts"},
        },
    ]
    graph = build_tool_graph(tools, Invoker())
    output = graph.invoke({"result": "", "goal": {"utterance": "Why was I charged $42?"}})
    assert [invoke["url"] for invoke, _ in calls] == [
        "http://tool-mock:3010/fees/explain",
        "http://tool-mock:3010/accounts",
    ]
    assert calls[0][1] == {"utterance": "Why was I charged $42?"}
    assert output["result"] == "from-http://tool-mock:3010/accounts"


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
            "invoke": {"method": "POST", "url": "http://tool-mock:3010/legal/clauses/search"},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke({"result": "", "goal": {"claim_id": "clm-1001"}})
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
            "invoke": {"method": "POST", "url": "http://tool-mock:3010/legal/memo"},
        }
    ]
    graph = build_tool_graph(tools, Invoker(), llm=Llm())
    output = graph.invoke(
        {"result": "", "goal": {"claim_id": "clm-1001"}, "notes": ["clause 4.2"]}
    )
    assert output["result"] == "Deny: exclusion applies."


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
            "invoke": {"method": "POST", "url": "http://tool-mock:3010/unused"},
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
            "invoke": {"method": "POST", "url": "http://tool-mock:3010/legal/playbook/search"},
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


def test_agent_kind_skips_http() -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("kind=agent must not POST jobs yet")

    graph = build_tool_graph(
        [
            {
                "id": "start_contract_review",
                "kind": "agent",
                "invoke": {
                    "method": "POST",
                    "url": "https://api-afd.internal/v1/jobs",
                },
            }
        ],
        Invoker(),
    )
    output = graph.invoke({"result": "", "goal": {"document_id": "doc-1"}, "notes": []})
    assert "skipped" in output["result"]


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

    class Llm:
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
            "invoke": {"method": "POST", "url": "http://tool-mock:3010/fees/explain"},
        }
    ]
    graph = build_agent_loop(tools, Invoker(), Llm())
    output = graph.invoke({"result": "", "goal": {"utterance": "Why $42?"}, "notes": []})
    assert calls == ["http://tool-mock:3010/fees/explain"]
    assert output["result"] == "Fee of $42 is the monthly account charge."
