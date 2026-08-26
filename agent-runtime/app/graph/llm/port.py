from typing import Any, Protocol


class LlmPort(Protocol):
    def complete(
        self, system: str, user: str, schema: dict[str, Any] | None = None
    ) -> str: ...
