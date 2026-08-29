from app.graph.llm import ProviderLlm, SeedStubLlm, _plain_text, llm_from_env


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


def test_seed_stub_asks_then_calls_lookup(monkeypatch) -> None:
    llm = SeedStubLlm()
    system = (
        "You are an agent with domain tools. Reply with exactly one of:\n"
        "Tools: escalate_to_human, lookup_order, lookup_order_by_customer, lookup_order_by_email"
    )
    asked = llm.complete(system, "goal: {'utterance': 'jacket damaged'}")
    assert asked.startswith("ASK ")
    called = llm.complete(
        system,
        "goal: {'utterance': 'jacket damaged'}\nprior stage outputs:\n- Please provide an order id\n- customer: ORD-77819",
    )
    assert called.startswith("CALL lookup_order")
    assert "ORD-77819" in called


def test_seed_stub_calls_domain_apis_after_lookup() -> None:
    llm = SeedStubLlm()
    system = (
        "You are an agent with domain tools.\n"
        "Tools: lookup_order, investigate_duplicate_charge, check_return_policy, escalate_to_human"
    )
    after_lookup = (
        "goal: {'utterance': 'charged twice, full refund'}\n"
        "prior stage outputs:\n"
        "- Order ORD-77819: Blue Jacket $149."
    )
    billing = llm.complete(system, after_lookup)
    assert billing.startswith("CALL investigate_duplicate_charge")
    assert "ORD-77819" in billing

    after_billing = after_lookup + "\n- No duplicate capture on ORD-77819."
    policy = llm.complete(system, after_billing)
    assert policy.startswith("CALL check_return_policy")

    after_policy = (
        after_billing
        + "\n- Policy returns-v7: eligible. Auto limit $75; $149 requires human escalation."
    )
    escalate = llm.complete(system, after_policy)
    assert escalate.startswith("CALL escalate_to_human")


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


def test_seed_stub_prefetch_overdraft_answer() -> None:
    llm = SeedStubLlm()
    user = (
        "goal: {'utterance': 'What is the overdraft fee on our Everyday account?'}\n"
        "packed chunks:\n"
        "- [fee-schedule:fs-everyday-od-1] Everyday Account overdraft fee: $10 per day\n"
        "- [product-disclosure:pd-everyday-od-1] Fees apply only with arranged overdraft"
    )
    text = llm.complete("Pattern 0. Cite chunk ids.", user)
    assert "$10" in text
    assert "[fee-schedule:fs-everyday-od-1]" in text


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
    monkeypatch.setenv("FABRIC_LLM_STUB", "1")
    assert isinstance(llm_from_env(), SeedStubLlm)
