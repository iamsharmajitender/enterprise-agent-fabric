from typing import Any, Literal

from pydantic import BaseModel, Field

from app.graph.agent_loop.parse import parse_agent_line

AgentAction = Literal["tool_call", "ask", "done"]


class AgentDecision(BaseModel):
    """Structured decision returned by the LLM on every agent-loop iteration."""

    action: AgentAction
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None


def text_to_decision(text: str) -> AgentDecision:
    """Convert legacy CALL/ASK/DONE text into an AgentDecision (tests and stubs)."""
    action, payload, call_args = parse_agent_line(text)
    if action == "ask":
        return AgentDecision(action="ask", message=payload or None)
    if action == "done":
        return AgentDecision(action="done", message=payload or None)
    return AgentDecision(
        action="tool_call",
        tool_name=payload or None,
        arguments=call_args,
    )
