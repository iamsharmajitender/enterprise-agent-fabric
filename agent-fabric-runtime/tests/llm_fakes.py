from typing import TypeVar

from pydantic import BaseModel

from app.graph.agent_loop.decision import AgentDecision, text_to_decision

T = TypeVar("T", bound=BaseModel)


class TextLlm:
    """Test helper: implement complete(); complete_structured() maps CALL/ASK/DONE text."""

    def complete_structured(self, system: str, user: str, schema: type[T]) -> T:
        if schema is not AgentDecision:
            raise TypeError(f"unsupported structured schema {schema!r}")
        return text_to_decision(self.complete(system, user))  # type: ignore[return-value]
