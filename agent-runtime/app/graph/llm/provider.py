"""Default LLM provider behind ``LlmPort``.

Today the backend is LangChain + Ollama (env ``OLLAMA_*``). Swap frameworks by
replacing ``_build_default_backend`` only — callers use ``ProviderLlm`` / ``llm_from_env``.
"""

import os
from typing import Any, Protocol

from app import telemetry
from app.graph.llm.text import plain_text

_DEFAULT_MODEL = "ollama:qwen3:8b"
_DEFAULT_SYSTEM = "Follow the user request. Reply with the result only."


class _ChatBackend(Protocol):
    def invoke(self, messages: list) -> Any: ...


class ProviderLlm:
    """Env-configured LLM completer (not tied to chat ingress or a specific vendor name)."""

    def __init__(self, backend: _ChatBackend | None = None) -> None:
        """Use an injected backend, or build the default provider from env."""
        self._backend = backend if backend is not None else _build_default_backend()

    def complete(self, system: str, user: str) -> str:
        """Run one completion and return plain text."""
        with telemetry.tracer().start_as_current_span("llm.complete") as span:
            span.set_attribute("llm.system", "provider")
            model = os.environ.get("OLLAMA_MODEL") or os.environ.get("FABRIC_LLM_MODEL") or _DEFAULT_MODEL
            span.set_attribute("llm.model", model)
            message = self._backend.invoke(
                [
                    ("system", system or _DEFAULT_SYSTEM),
                    ("human", user),
                ]
            )
            return plain_text(getattr(message, "content", message))


def _build_default_backend() -> _ChatBackend:
    """Construct the default chat backend.

    Implementation detail: LangChain ``init_chat_model`` + Ollama defaults.
    Replace this function when moving to another SDK or host.
    """
    # init_chat_model: https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model
    # ChatOllama maps max output to num_predict and HTTP timeout to client_kwargs:
    # https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama
    from langchain.chat_models import init_chat_model

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
    model = os.environ.get("OLLAMA_MODEL") or os.environ.get("FABRIC_LLM_MODEL") or _DEFAULT_MODEL
    return init_chat_model(model, **kwargs)
