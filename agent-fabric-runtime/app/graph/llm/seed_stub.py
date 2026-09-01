import ast
import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel

from app import telemetry
from app.graph.agent_loop.decision import AgentDecision, text_to_decision
from app.graph.llm.schema import dump_structured, stub_payload
from app.graph.payload import grounding_ask_message, schema_required

T = TypeVar("T", bound=BaseModel)

_TOOLS_LINE = re.compile(r"(?m)^Tools:\s*(.+)$")
_AVAILABLE_TOOL_LINE = re.compile(r"^- ([^:]+):")


class SeedStubLlm:
    """Deterministic local LLM for agent loops and synthesis without Ollama."""

    def __init__(self) -> None:
        self._agent_turns: dict[str, int] = {}

    def complete(self, system: str, user: str, schema: dict[str, Any] | None = None) -> str:
        """JSON stub when a schema is bound; legacy text protocol for old prompts."""
        with telemetry.tracer().start_as_current_span("llm.complete") as span:
            span.set_attribute("llm.system", "stub")
            span.set_attribute("llm.model", "seed-stub")
            span.set_attribute("llm.structured", bool(schema))
            if schema:
                return dump_structured(stub_payload(schema), schema)
            if "You are an agent with domain tools" in (system or ""):
                tools = _tools_from_legacy_system(system)
                turn = self._agent_turns.get(system, 0) + 1
                self._agent_turns[system] = turn
                if turn == 1 and tools:
                    return _call_line(system, user, tools[0])
                answer = _last_prior_note(user) or "ok"
                return f"DONE {answer}"
            grounded = _prefetch_synthesis_answer(user)
            if grounded:
                return grounded
            return "ok"

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[T],
    ) -> T:
        """Return a deterministic AgentDecision for Pattern 1 agent loops."""
        with telemetry.tracer().start_as_current_span("llm.complete") as span:
            span.set_attribute("llm.system", "stub")
            span.set_attribute("llm.model", "seed-stub")
            span.set_attribute("llm.structured", True)
            span.set_attribute("llm.schema", schema.__name__)
            if schema is AgentDecision:
                return self._agent_decision(system, user)  # type: ignore[return-value]
            if issubclass(schema, BaseModel):
                payload = stub_payload(schema.model_json_schema())
                return schema.model_validate(payload)
            raise RuntimeError(f"seed stub does not support structured schema {schema!r}")

    def _agent_decision(self, system: str, user: str) -> AgentDecision:
        tools = _tools_from_available_section(system) or _tools_from_legacy_system(system)
        turn = self._agent_turns.get(system, 0) + 1
        self._agent_turns[system] = turn
        if "customer:" in user and tools:
            tool_id = tools[0]
            args = _call_args(system, user, tool_id)
            return AgentDecision(action="tool_call", tool_name=tool_id, arguments=args)
        if turn == 1 and tools:
            tool_id = tools[0]
            schema = _schemas_from_system(system).get(tool_id)
            args = _call_args(system, user, tool_id)
            if schema and _needs_customer_locator(schema, args, user):
                return AgentDecision(
                    action="ask",
                    message=grounding_ask_message(tool_id, schema),
                )
            return AgentDecision(action="tool_call", tool_name=tool_id, arguments=args)
        answer = _last_prior_note(user) or "ok"
        return AgentDecision(action="done", message=answer)


def _tools_from_legacy_system(system: str) -> list[str]:
    match = _TOOLS_LINE.search(system or "")
    if match is None:
        return []
    raw = match.group(1).strip()
    if raw == "(none)" or not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _tools_from_available_section(system: str) -> list[str]:
    lines = (system or "").splitlines()
    in_block = False
    found: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "Available tools:":
            in_block = True
            continue
        if not in_block:
            continue
        if stripped.startswith("Tool input schemas:") or stripped.startswith("Rules:"):
            break
        match = _AVAILABLE_TOOL_LINE.match(stripped)
        if not match:
            if stripped and not stripped.startswith("- "):
                break
            continue
        tool_id = match.group(1).strip()
        if tool_id and tool_id != "(none)":
            found.append(tool_id)
    return sorted(found)


def _schemas_from_system(system: str) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    in_block = False
    for line in (system or "").splitlines():
        stripped = line.strip()
        if stripped == "Tool input schemas:":
            in_block = True
            continue
        if not in_block:
            continue
        if not line.startswith("- "):
            if stripped:
                break
            continue
        tool_id, _, rest = line[2:].partition(": ")
        tool_id = tool_id.strip()
        if not tool_id or not rest.strip():
            continue
        try:
            parsed = json.loads(rest.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            schemas[tool_id] = parsed
    return schemas


def _goal_from_user(user: str) -> dict[str, Any]:
    for line in (user or "").splitlines():
        if not line.startswith("goal:"):
            continue
        raw = line[5:].strip()
        if not raw:
            return {}
        try:
            parsed = ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _example_args_from_host(system: str, tool_id: str) -> dict[str, Any]:
    pattern = rf"(?i)(?:call\s+)?{re.escape(tool_id)}\b[^\n{{}}]*(\{{[^{{}}]+\}})"
    found = re.search(pattern, system or "")
    if not found:
        return {}
    try:
        parsed = json.loads(found.group(1))
    except json.JSONDecodeError:
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _call_args(system: str, user: str, tool_id: str) -> dict[str, Any]:
    schema = _schemas_from_system(system).get(tool_id)
    if not schema:
        return _example_args_from_host(system, tool_id)
    args = dict(_example_args_from_host(system, tool_id))
    goal = _goal_from_user(user)
    for key in schema_required(schema):
        if key in goal and goal[key] is not None:
            args[key] = goal[key]
    for line in (user or "").splitlines():
        if not line.startswith("- customer:"):
            continue
        reply = line[len("- customer:") :].strip()
        if reply:
            for key in schema_required(schema):
                args.setdefault(key, reply)
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    stubs = stub_payload(schema)
    for key in schema_required(schema):
        if key in args:
            continue
        spec = props.get(key) if isinstance(props, dict) else None
        if isinstance(spec, dict) and spec.get("x-ground-in-user-context"):
            continue
        if key in stubs:
            args[key] = stubs[key]
    return args


def _needs_customer_locator(schema: dict[str, Any], args: dict[str, Any], user: str) -> bool:
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    context = user
    for key in schema_required(schema):
        spec = props.get(key) if isinstance(props, dict) else None
        if not isinstance(spec, dict) or not spec.get("x-ground-in-user-context"):
            continue
        value = args.get(key)
        if value is None or str(value).strip() == "":
            return True
        if str(value) not in context:
            return True
    return False


def _call_line(system: str, user: str, tool_id: str) -> str:
    args = _call_args(system, user, tool_id)
    if args:
        return f"CALL {tool_id}\n{json.dumps(args, separators=(',', ':'), ensure_ascii=False)}"
    return f"CALL {tool_id}"


def _last_prior_note(user: str) -> str:
    notes: list[str] = []
    for line in (user or "").splitlines():
        if line.startswith("- "):
            notes.append(line[2:].strip())
    return notes[-1] if notes else ""


def _prefetch_synthesis_answer(user: str) -> str:
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
