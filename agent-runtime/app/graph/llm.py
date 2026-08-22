import os
from typing import Any, Protocol

from app import telemetry
from langchain.chat_models import init_chat_model

# init_chat_model: https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model
# ChatOllama maps max output to num_predict and HTTP timeout to client_kwargs:
# https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama
_DEFAULT_MODEL = "ollama:qwen3:8b"
_DEFAULT_SYSTEM = "Follow the user request. Reply with the result only."


class LlmPort(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class LangChainChat:
    def __init__(self, model: Any | None = None) -> None:
        """Use an injected chat model, or build the default Ollama client."""
        self._model = model if model is not None else _build_model()

    def complete(self, system: str, user: str) -> str:
        """Run one chat completion and return plain text (think-tags stripped)."""
        with telemetry.tracer().start_as_current_span("llm.complete") as span:
            span.set_attribute("llm.system", "ollama")
            model = os.environ.get("OLLAMA_MODEL") or _DEFAULT_MODEL
            span.set_attribute("llm.model", model)
            message = self._model.invoke(
                [
                    ("system", system or _DEFAULT_SYSTEM),
                    ("human", user),
                ]
            )
            return _plain_text(getattr(message, "content", message))


def _build_model() -> Any:
    """Construct the LangChain chat model from env (OLLAMA_BASE_URL)."""
    kwargs: dict[str, Any] = {
        "temperature": 0.5,
        "timeout": 300,
        "max_tokens": 25000,
        "num_predict": 25000,
        "client_kwargs": {"timeout": 300.0},
    }
    base_url = os.environ.get("OLLAMA_BASE_URL", "").strip()
    if base_url:
        kwargs["base_url"] = base_url
    return init_chat_model(_DEFAULT_MODEL, **kwargs)


def _plain_text(content: Any) -> str:
    """Flatten chat content to a string and drop Qwen `</think>` preamble."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
        text = "".join(parts)
    else:
        text = "" if content is None else str(content)
    marker = "</think>"
    if marker in text:
        text = text.split(marker, 1)[-1]
    return text.strip()
