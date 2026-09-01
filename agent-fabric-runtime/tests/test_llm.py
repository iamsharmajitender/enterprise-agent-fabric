from app.graph.llm import ProviderLlm, SeedStubLlm, _plain_text, llm_from_env
from app.graph.llm.instrumented import TelemetryLlm


def test_plain_text_strips_qwen_think_tags() -> None:
    assert _plain_text("keep me") == "keep me"
    assert _plain_text("<think>plan</think>\nexclusion 4.2") == "exclusion 4.2"


def test_provider_llm_invokes_system_and_human() -> None:
    seen: list[object] = []

    class Backend:
        def invoke(self, messages: list) -> object:
            seen.append(messages)

            class Reply:
                content = "exclusion 4.2"

            return Reply()

    text = ProviderLlm(backend=Backend()).complete("Write the query", "goal: clm-1001")
    assert text == "exclusion 4.2"
    assert seen[0][0] == ("system", "Write the query")
    assert seen[0][1][0] == "human"


def test_seed_stub_calls_then_dones() -> None:
    llm = SeedStubLlm()
    system = (
        "You are an agent with domain tools. Reply with exactly one line:\n"
        "Tools: draft_memo"
    )
    assert llm.complete(system, "goal: {'case_id': 'frd-1'}") == "CALL draft_memo"
    assert llm.complete(
        system, "goal: {'case_id': 'frd-1'}\nprior stage outputs:\n- memo text"
    ) == "DONE memo text"


def test_seed_stub_calls_first_tool_then_dones() -> None:
    llm = SeedStubLlm()
    system = (
        "You are an agent with domain tools. Reply with exactly one of:\n"
        "Tools: fetch_record, check_policy"
    )
    assert llm.complete(system, "goal: {'utterance': 'need help'}") == "CALL fetch_record"
    assert llm.complete(
        system,
        "goal: {'utterance': 'need help'}\nprior stage outputs:\n- Record REC-77819: widget.",
    ) == "DONE Record REC-77819: widget."


def test_seed_stub_call_includes_schema_args() -> None:
    llm = SeedStubLlm()
    system = (
        "You are an agent with domain tools. Reply with exactly one of:\n"
        "CALL account_fee_lookup with {\"account_id\":\"acct-4412\"} when needed.\n"
        "Tools: account_fee_lookup\n"
        "Tool input schemas:\n"
        '- account_fee_lookup: {"type":"object","required":["account_id"],'
        '"properties":{"account_id":{"type":"string"}}}'
    )
    text = llm.complete(system, "goal: {'utterance': 'Why was I charged $42?'}")
    assert text == 'CALL account_fee_lookup\n{"account_id":"acct-4412"}'


def test_provider_llm_complete_structured_agent_decision() -> None:
    from app.graph.agent_loop.decision import AgentDecision

    class Parsed(AgentDecision):
        pass

    class Structured:
        def invoke(self, messages: list) -> object:
            return AgentDecision(
                action="tool_call",
                tool_name="fetch_record",
                arguments={"record_id": "REC-1"},
            )

    class Backend:
        def invoke(self, messages: list) -> object:
            raise AssertionError("structured path must not use plain invoke")

        def with_structured_output(self, schema: object) -> Structured:
            assert schema is AgentDecision
            return Structured()

    decision = ProviderLlm(backend=Backend()).complete_structured(
        "Decide next action.",
        "goal: {}",
        AgentDecision,
    )
    assert decision.action == "tool_call"
    assert decision.tool_name == "fetch_record"
    assert decision.arguments == {"record_id": "REC-1"}


def test_seed_stub_complete_structured_agent_decision() -> None:
    from app.graph.agent_loop.decision import AgentDecision
    from app.graph.agent_loop.prompt import build_agent_prompt

    llm = SeedStubLlm()
    tools = [
        {
            "id": "fetch_record",
            "description": "Fetch a record",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {"record_id": {"type": "string"}},
            },
        }
    ]
    prompt = build_agent_prompt(tools, "Route host.")
    first = llm.complete_structured(prompt, "goal: {'utterance': 'help'}", AgentDecision)
    assert first.action == "tool_call"
    assert first.tool_name == "fetch_record"
    assert first.arguments == {"record_id": "stub"}
    second = llm.complete_structured(
        prompt,
        "goal: {'utterance': 'help'}\nprior stage outputs:\n- Record REC-1: widget.",
        AgentDecision,
    )
    assert second.action == "done"
    assert second.message == "Record REC-1: widget."


def test_seed_stub_asks_when_grounded_order_id_missing() -> None:
    from app.graph.agent_loop.decision import AgentDecision
    from app.graph.agent_loop.prompt import build_agent_prompt

    llm = SeedStubLlm()
    tools = [
        {
            "id": "lookup_order_by_order_id",
            "description": "Lookup order",
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
        }
    ]
    prompt = build_agent_prompt(tools, "ShopAssist host.")
    decision = llm.complete_structured(
        prompt,
        "goal: {'utterance': 'My jacket arrived damaged'}",
        AgentDecision,
    )
    assert decision.action == "ask"
    assert "order number" in (decision.message or "").lower()


def test_provider_llm_binds_structured_output() -> None:
    seen: list[object] = []

    class Parsed:
        def model_dump(self, mode: str = "python") -> dict:
            return {"merchant": "Acme", "amount": 45.36, "date": "2026-08-12"}

    class Structured:
        def invoke(self, messages: list) -> object:
            seen.append(("invoke", messages))
            return Parsed()

    class Backend:
        def invoke(self, messages: list) -> object:
            raise AssertionError("structured path must not use plain invoke")

        def with_structured_output(self, schema: object) -> Structured:
            seen.append(("bind", schema))
            return Structured()

    text = ProviderLlm(backend=Backend()).complete(
        "Return JSON only.",
        "goal: {'doc_id': 'r-1'}",
        schema={
            "title": "extract_fields",
            "type": "object",
            "required": ["merchant", "amount", "date"],
            "properties": {
                "merchant": {"type": "string"},
                "amount": {"type": "number"},
                "date": {"type": "string"},
            },
        },
    )
    assert text == '{"merchant":"Acme","amount":45.36,"date":"2026-08-12"}'
    assert seen[0][0] == "bind"
    assert seen[1][0] == "invoke"


def test_seed_stub_prefetch_synthesis_echoes_chunks() -> None:
    llm = SeedStubLlm()
    user = (
        "goal: {'utterance': 'Summarize the fee schedule.'}\n"
        "packed chunks:\n"
        "- [fee-schedule:fs-1] Daily fee is $10 per day\n"
        "- [product-disclosure:pd-1] Fees apply with approved facility"
    )
    text = llm.complete("Pattern 0. Cite chunk ids.", user)
    assert "$10 per day" in text
    assert "[fee-schedule:fs-1]" in text


def test_seed_stub_returns_schema_json() -> None:
    llm = SeedStubLlm()
    text = llm.complete(
        "Return JSON only.",
        "goal: {}",
        schema={
            "type": "object",
            "required": ["merchant", "amount", "date"],
            "properties": {
                "merchant": {"type": "string"},
                "amount": {"type": "number"},
                "date": {"type": "string"},
            },
        },
    )
    assert text == '{"merchant":"stub","amount":0.0,"date":"stub"}'


def test_seed_stub_unwraps_text_envelope() -> None:
    llm = SeedStubLlm()
    text = llm.complete(
        "Write the confirm",
        "goal: {}",
        schema={
            "type": "object",
            "required": ["text"],
            "properties": {"text": {"type": "string"}},
        },
    )
    assert text == "stub"


def test_llm_from_env_prefers_stub(monkeypatch) -> None:
    from app.graph.llm.retry import RetryLlm

    monkeypatch.setenv("FABRIC_LLM_STUB", "1")
    llm = llm_from_env()
    assert isinstance(llm, TelemetryLlm)
    assert isinstance(llm._inner, RetryLlm)
    assert isinstance(llm._inner._inner, SeedStubLlm)
