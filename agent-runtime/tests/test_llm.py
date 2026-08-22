from app.graph.llm import LangChainChat, _plain_text


def test_plain_text_strips_qwen_think_tags() -> None:
    assert _plain_text("keep me") == "keep me"
    assert _plain_text("<think>plan</think>\nexclusion 4.2") == "exclusion 4.2"


def test_langchain_chat_invokes_system_and_human() -> None:
    seen: list[object] = []

    class Model:
        def invoke(self, messages: list) -> object:
            seen.append(messages)

            class Reply:
                content = "exclusion 4.2"

            return Reply()

    text = LangChainChat(model=Model()).complete("Write the query", "goal: clm-1001")
    assert text == "exclusion 4.2"
    assert seen[0][0] == ("system", "Write the query")
    assert seen[0][1][0] == "human"
