import re
from typing import Any

from app import telemetry
from app.graph.llm.schema import dump_structured, stub_payload

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
                    return f"CALL {tools[0]}"
                answer = _last_prior_note(user) or "ok"
                return f"DONE {answer}"
            grounded = _prefetch_synthesis_answer(user)
            if grounded:
                return grounded
            return "ok"


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


def _prefetch_synthesis_answer(user: str) -> str:
    """Pattern 0 synthesis stub: echo packed chunk text when present."""
    lines: list[str] = []
    in_chunks = False
    for line in (user or "").splitlines():
        lowered = line.strip().lower()
        if lowered == "packed chunks:":
            in_chunks = True
            continue
        if in_chunks:
            if line.startswith("prior stage outputs:"):
                break
            if line.startswith("- "):
                lines.append(line[2:].strip())
    if not lines:
        return ""
    return " ".join(lines)
