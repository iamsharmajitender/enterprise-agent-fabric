from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LlmPort(Protocol):
    def complete(
        self, system: str, user: str, schema: dict[str, Any] | None = None
    ) -> str: ...

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[T],
    ) -> T: ...
