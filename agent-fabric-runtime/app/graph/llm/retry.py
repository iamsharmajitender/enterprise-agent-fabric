"""Retry wrapper for ``LlmPort`` with exponential backoff on transient failures."""

from __future__ import annotations

import os
import random
import time
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from app.graph.llm.port import LlmPort

T = TypeVar("T", bound=BaseModel)

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BASE_S = 1.0
_DEFAULT_MAX_BACKOFF_S = 30.0

_RETRYABLE_NAME_TOKENS = frozenset({"timeout", "connection", "connect", "readerror", "network"})


def retry_config() -> tuple[int, float, float]:
    """Read FABRIC_LLM_RETRY_* env (max attempts, base delay s, cap s)."""
    max_attempts = max(1, int(os.environ.get("FABRIC_LLM_RETRY_MAX", str(_DEFAULT_MAX_ATTEMPTS))))
    base_s = max(0.0, float(os.environ.get("FABRIC_LLM_RETRY_BASE_S", str(_DEFAULT_BASE_S))))
    max_backoff_s = max(
        base_s,
        float(os.environ.get("FABRIC_LLM_RETRY_MAX_BACKOFF_S", str(_DEFAULT_MAX_BACKOFF_S))),
    )
    return max_attempts, base_s, max_backoff_s


def is_retryable_llm_error(exc: BaseException) -> bool:
    """True for transient provider/network failures; false for logic/config errors."""
    if isinstance(exc, RuntimeError):
        return False
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    try:
        import httpx

        if isinstance(
            exc,
            (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.ReadError,
                httpx.RemoteProtocolError,
            ),
        ):
            return True
    except ImportError:
        pass
    name = type(exc).__name__.lower()
    return any(token in name for token in _RETRYABLE_NAME_TOKENS)


def backoff_seconds(attempt: int, base_s: float, max_s: float) -> float:
    """Exponential delay with jitter; attempt is 0 on the first retry."""
    delay = min(max_s, base_s * (2**attempt))
    return delay * (0.5 + random.random() * 0.5)


class RetryLlm:
    """Wrap ``LlmPort``; retry transient provider failures with exponential backoff."""

    def __init__(
        self,
        inner: LlmPort,
        *,
        max_attempts: int | None = None,
        base_s: float | None = None,
        max_backoff_s: float | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        cfg_max, cfg_base, cfg_cap = retry_config()
        self._inner = inner
        self._max_attempts = max_attempts if max_attempts is not None else cfg_max
        self._base_s = base_s if base_s is not None else cfg_base
        self._max_backoff_s = max_backoff_s if max_backoff_s is not None else cfg_cap
        self._sleep = sleep if sleep is not None else time.sleep

    def complete(self, system: str, user: str, schema: dict[str, Any] | None = None) -> str:
        return self._with_retry(lambda: self._inner.complete(system, user, schema=schema))

    def complete_structured(self, system: str, user: str, schema: type[T]) -> T:
        return self._with_retry(lambda: self._inner.complete_structured(system, user, schema))

    def _with_retry(self, call: Callable[[], Any]) -> Any:
        last: BaseException | None = None
        for attempt in range(self._max_attempts):
            try:
                return call()
            except Exception as exc:
                last = exc
                if attempt + 1 >= self._max_attempts or not is_retryable_llm_error(exc):
                    raise
                self._sleep(backoff_seconds(attempt, self._base_s, self._max_backoff_s))
        raise RuntimeError("retry loop exhausted") from last
