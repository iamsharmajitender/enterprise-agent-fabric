import re
from typing import Any

from app import telemetry
from app.graph.llm.schema import dump_structured, stub_payload

_FEE_CANNED = "Fee of $42 is the monthly account charge."
_TOOLS_LINE = re.compile(r"(?m)^Tools:\s*(.+)$")


class SeedStubLlm:
    """Deterministic local LLM so Pattern 1 CALL/DONE and synthesis finish without Ollama."""

    def __init__(self) -> None:
        self._agent_turns: dict[str, int] = {}

    def complete(self, system: str, user: str, schema: dict[str, Any] | None = None) -> str:
        """One CALL then DONE for agent loops; JSON stub when a schema is bound."""
        with telemetry.tracer().start_as_current_span("llm.complete") as span:
            span.set_attribute("llm.system", "stub")
            span.set_attribute("llm.model", "seed-stub")
            span.set_attribute("llm.structured", bool(schema))
            if schema:
                return dump_structured(stub_payload(schema), schema)
            if "You are an agent with domain tools" in (system or ""):
                tools = _tools_from_system(system)
                turn = self._agent_turns.get(system, 0) + 1
                self._agent_turns[system] = turn
                if turn == 1 and tools:
                    first = tools[0]
                    # Chat fee_explain goal is utterance-only; skip CALL when account_id is absent.
                    if first == "account_fee_lookup" and "account_id" not in (user or "").lower():
                        return f"DONE {_fee_or_ok(user)}"
                    return f"CALL {first}"
                answer = _last_prior_note(user) or _fee_or_ok(user)
                return f"DONE {answer}"
            return _fee_or_ok(user)


def _tools_from_system(system: str) -> list[str]:
    """Parse `Tools: a, b` from the Pattern 1 system prompt."""
    match = _TOOLS_LINE.search(system or "")
    if match is None:
        return []
    raw = match.group(1).strip()
    if raw == "(none)" or not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _last_prior_note(user: str) -> str:
    """Return the last `- note` line from the agent user blob, if any."""
    notes: list[str] = []
    for line in (user or "").splitlines():
        if line.startswith("- "):
            notes.append(line[2:].strip())
    return notes[-1] if notes else ""


def _fee_or_ok(user: str) -> str:
    """Canned fee line when the goal looks like fee_explain; otherwise a short stub."""
    blob = (user or "").lower()
    if "account_id" in blob or "fee" in blob or "charged" in blob:
        return _FEE_CANNED
    return "ok"
