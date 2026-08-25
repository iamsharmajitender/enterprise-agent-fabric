from typing import Protocol


class LlmPort(Protocol):
    def complete(self, system: str, user: str) -> str: ...
