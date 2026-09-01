import pytest

from app.graph.llm.retry import RetryLlm, backoff_seconds, is_retryable_llm_error


class _FlakyLlm:
    def __init__(self, failures: list[BaseException], result: str = "ok") -> None:
        self._failures = list(failures)
        self._result = result
        self.attempts = 0

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.attempts += 1
        if self._failures:
            raise self._failures.pop(0)
        return self._result

    def complete_structured(self, system: str, user: str, schema: type) -> object:
        self.attempts += 1
        if self._failures:
            raise self._failures.pop(0)
        return schema.model_validate({"action": "done", "message": self._result})


def test_is_retryable_llm_error() -> None:
    assert is_retryable_llm_error(TimeoutError())
    assert is_retryable_llm_error(ConnectionError())
    assert not is_retryable_llm_error(RuntimeError("backend does not support structured output"))

    class ReadTimeoutError(Exception):
        pass

    assert is_retryable_llm_error(ReadTimeoutError())


def test_backoff_seconds_grows_with_attempt() -> None:
    first = backoff_seconds(0, 1.0, 30.0)
    second = backoff_seconds(1, 1.0, 30.0)
    assert 0.5 <= first <= 1.0
    assert 1.0 <= second <= 2.0


def test_retry_llm_recovers_after_transient_failure() -> None:
    sleeps: list[float] = []

    llm = RetryLlm(
        _FlakyLlm([TimeoutError()], result="answer"),
        max_attempts=3,
        base_s=1.0,
        max_backoff_s=4.0,
        sleep=sleeps.append,
    )
    assert llm.complete("sys", "user") == "answer"
    assert llm._inner.attempts == 2
    assert len(sleeps) == 1


def test_retry_llm_does_not_retry_runtime_error() -> None:
    llm = RetryLlm(
        _FlakyLlm([RuntimeError("config")]),
        max_attempts=3,
        sleep=lambda _: pytest.fail("should not sleep"),
    )
    with pytest.raises(RuntimeError, match="config"):
        llm.complete("sys", "user")
    assert llm._inner.attempts == 1


def test_retry_llm_exhausts_attempts() -> None:
    sleeps: list[float] = []
    llm = RetryLlm(
        _FlakyLlm([TimeoutError(), TimeoutError(), TimeoutError()]),
        max_attempts=3,
        sleep=sleeps.append,
    )
    with pytest.raises(TimeoutError):
        llm.complete("sys", "user")
    assert llm._inner.attempts == 3
    assert len(sleeps) == 2
