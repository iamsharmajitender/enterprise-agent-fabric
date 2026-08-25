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


def test_llm_from_env_prefers_stub(monkeypatch) -> None:
    monkeypatch.setenv("FABRIC_LLM_STUB", "1")
    assert isinstance(llm_from_env(), SeedStubLlm)
