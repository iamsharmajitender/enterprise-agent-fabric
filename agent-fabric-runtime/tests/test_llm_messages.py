from app.graph.llm.messages import effective_system, llm_messages_preview


def test_llm_messages_preview_includes_system_and_user() -> None:
    preview = llm_messages_preview(
        "Pattern 0 synthesis.",
        "goal: {'utterance': 'fee?'}\npacked chunks:\n- chunk one",
    )
    assert preview["messages"] == [
        {"role": "system", "content": "Pattern 0 synthesis."},
        {"role": "user", "content": "goal: {'utterance': 'fee?'}\npacked chunks:\n- chunk one"},
    ]


def test_effective_system_uses_default_when_blank() -> None:
    assert effective_system("") == "Follow the user request. Reply with the result only."


def test_llm_messages_preview_structured_schema() -> None:
    schema = {
        "title": "StageOutput",
        "type": "object",
        "properties": {"text": {"type": "string"}},
    }
    preview = llm_messages_preview(
        "system",
        "user",
        structured=True,
        schema_name="StageOutput",
        output_schema=schema,
    )
    assert preview["structured"] is True
    assert preview["schema_name"] == "StageOutput"
    assert preview["output_schema"] == schema
