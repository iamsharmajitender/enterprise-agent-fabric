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
