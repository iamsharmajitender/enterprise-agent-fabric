"""Default LLM provider behind ``LlmPort``.

Today the backend is LangChain + Ollama (env ``OLLAMA_*``). Swap frameworks by
replacing ``_build_default_backend`` only — callers use ``ProviderLlm`` / ``llm_from_env``.
"""

import os
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from app import telemetry
from app.graph.llm.schema import dump_structured, model_from_json_schema
from app.graph.llm.text import plain_text

T = TypeVar("T", bound=BaseModel)

_DEFAULT_MODEL = "ollama:qwen3:14b"
from app.graph.llm.messages import DEFAULT_SYSTEM as _DEFAULT_SYSTEM


class _ChatBackend(Protocol):
    def invoke(self, messages: list) -> Any: ...


class ProviderLlm:
    """Env-configured LLM completer (not tied to chat ingress or a specific vendor name)."""

    def __init__(self, backend: _ChatBackend | None = None) -> None:
        """Use an injected backend, or build the default provider from env."""
        self._backend = backend if backend is not None else _build_default_backend()

    def complete(self, system: str, user: str, schema: dict[str, Any] | None = None) -> str:
        """Run one completion. With schema, bind structured output and return JSON."""
        with telemetry.tracer().start_as_current_span("llm.complete") as span:
            span.set_attribute("llm.system", "provider")
            model = os.environ.get("OLLAMA_MODEL") or os.environ.get("FABRIC_LLM_MODEL") or _DEFAULT_MODEL
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.structured", bool(schema))
            messages = [
                ("system", system or _DEFAULT_SYSTEM),
                ("human", user),
            ]
            if schema:
                return dump_structured(_structured_invoke(self._backend, schema, messages), schema)
            message = self._backend.invoke(messages)
            return plain_text(getattr(message, "content", message))

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[T],
    ) -> T:
        """Run one completion with a Pydantic schema bound via the chat backend."""
        with telemetry.tracer().start_as_current_span("llm.complete") as span:
            span.set_attribute("llm.system", "provider")
            model = os.environ.get("OLLAMA_MODEL") or os.environ.get("FABRIC_LLM_MODEL") or _DEFAULT_MODEL
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.structured", True)
            span.set_attribute("llm.schema", schema.__name__)
            messages = [
                ("system", system or _DEFAULT_SYSTEM),
                ("human", user),
            ]
            bind = getattr(self._backend, "with_structured_output", None)
            if bind is None:
                raise RuntimeError("llm backend does not support structured output")
            structured = bind(schema)
            result = structured.invoke(messages)
            if isinstance(result, schema):
                return result
            if isinstance(result, BaseModel):
                return schema.model_validate(result.model_dump())
            if isinstance(result, dict):
                return schema.model_validate(result)
            raise RuntimeError(f"structured llm returned unexpected type {type(result)!r}")


def _structured_invoke(backend: Any, schema: dict[str, Any], messages: list) -> Any:
    """Bind the backend with with_structured_output; fail if the backend cannot.

    ChatOllama default method is json_schema (Ollama structured outputs), not an
    OpenAI-only API. Do not pass method= so the provider keeps its default.
    Source: https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama/with_structured_output
    """
    bind = getattr(backend, "with_structured_output", None)
    if bind is None:
        raise RuntimeError("llm backend does not support structured output")
    title = str(schema.get("title") or "StageOutput")
    structured = bind(model_from_json_schema(schema, name=title))
    return structured.invoke(messages)


def _build_default_backend() -> _ChatBackend:
    """Construct the default chat backend.

    Implementation detail: LangChain ``init_chat_model`` + Ollama defaults.
    Replace this function when moving to another SDK or host.
    """
    # init_chat_model: https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model
    # ChatOllama maps max output to num_predict and HTTP timeout to client_kwargs:
    # https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama
    from langchain.chat_models import init_chat_model

    model = os.environ.get("OLLAMA_MODEL") or os.environ.get("FABRIC_LLM_MODEL") or _DEFAULT_MODEL
    kwargs: dict[str, Any] = {
        "temperature": 0.1,
        "timeout": 300,
        "max_tokens": 4096,
    }
    if model.startswith("ollama:"):
        kwargs["num_predict"] = 4096
        kwargs["client_kwargs"] = {"timeout": 300.0}
        base_url = os.environ.get("OLLAMA_BASE_URL", "").strip()
        if base_url:
            kwargs["base_url"] = base_url
    return init_chat_model(model, **kwargs)
