"""Telemetry wrapper for ``LlmPort`` — emits run.llm.* business events."""

from __future__ import annotations

import os
import time
from typing import Any, TypeVar

from pydantic import BaseModel

from app import telemetry
from app.graph.llm.port import LlmPort

T = TypeVar("T", bound=BaseModel)

_DEFAULT_MODEL = "ollama:qwen3:14b"


def llm_model_name() -> str:
    """Resolved model label for run.llm.* events."""
    if os.environ.get("FABRIC_LLM_STUB", "").strip().lower() in {"1", "true", "yes", "on"}:
        return "seed-stub"
    return (
        os.environ.get("OLLAMA_MODEL")
        or os.environ.get("FABRIC_LLM_MODEL")
        or _DEFAULT_MODEL
    )


def _response_preview(result: Any) -> Any:
    if isinstance(result, BaseModel):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    return str(result)


class TelemetryLlm:
    """Wrap an ``LlmPort`` and emit structured run.llm.* logs for each call."""

    def __init__(self, inner: LlmPort) -> None:
        self._inner = inner
        self._model = llm_model_name()

    def complete(self, system: str, user: str, schema: dict[str, Any] | None = None) -> str:
        schema_name = str(schema.get("title") or "") if schema else None
        structured = bool(schema)
        telemetry.emit_llm_started(
            system,
            user,
            structured=structured,
            schema_name=schema_name or None,
            output_schema=schema,
            llm_model=self._model,
        )
        start = time.monotonic()
        try:
            result = self._inner.complete(system, user, schema=schema)
        except RuntimeError:
            telemetry.emit_llm_failed(
                system,
                user,
                "runtime_error",
                structured=structured,
                schema_name=schema_name or None,
                output_schema=schema,
                llm_model=self._model,
            )
            raise
        except Exception:
            telemetry.emit_llm_failed(
                system,
                user,
                "llm_error",
                structured=structured,
                schema_name=schema_name or None,
                output_schema=schema,
                llm_model=self._model,
            )
            raise
        latency_ms = max(0, int((time.monotonic() - start) * 1000))
        telemetry.emit_llm_completed(result, latency_ms=latency_ms, llm_model=self._model)
        return result

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[T],
    ) -> T:
        schema_name = schema.__name__
        output_schema = schema.model_json_schema()
        telemetry.emit_llm_started(
            system,
            user,
            structured=True,
            schema_name=schema_name,
            output_schema=output_schema,
            llm_model=self._model,
        )
        start = time.monotonic()
        try:
            result = self._inner.complete_structured(system, user, schema)
        except RuntimeError:
            telemetry.emit_llm_failed(
                system,
                user,
                "runtime_error",
                structured=True,
                schema_name=schema_name,
                output_schema=output_schema,
                llm_model=self._model,
            )
            raise
        except Exception:
            telemetry.emit_llm_failed(
                system,
                user,
                "llm_error",
                structured=True,
                schema_name=schema_name,
                output_schema=output_schema,
                llm_model=self._model,
            )
            raise
        latency_ms = max(0, int((time.monotonic() - start) * 1000))
        telemetry.emit_llm_completed(
            _response_preview(result),
            latency_ms=latency_ms,
            llm_model=self._model,
        )
        return result
