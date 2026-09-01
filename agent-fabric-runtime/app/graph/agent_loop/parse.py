import json
from typing import Any, Literal

AgentAction = Literal["call", "ask", "done"]


def parse_json_object(raw: str) -> dict[str, Any] | None:
    """Return a dict if raw is a JSON object, else None."""
    text = (raw or "").strip()
    if not text.startswith("{"):
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def parse_agent_line(text: str) -> tuple[AgentAction, str, dict[str, Any]]:
    """Parse CALL / ASK / DONE. CALL may carry a JSON object of tool args."""
    blob = (text or "").strip()
    if not blob:
        return "done", "", {}
    lines = [line.strip() for line in blob.splitlines() if line.strip()]
    first = lines[0]
    head, _, rest = first.partition(" ")
    token = head.strip().upper()
    if token == "CALL":
        tool_id = rest.strip().split()[0] if rest.strip() else ""
        leftover = rest.strip()[len(tool_id) :].strip() if tool_id else ""
        args = parse_json_object(leftover) or {}
        if not args and len(lines) > 1:
            args = parse_json_object("\n".join(lines[1:])) or {}
        if not tool_id:
            raise RuntimeError("CALL missing tool id")
        return "call", tool_id, args
    if token == "ASK":
        return "ask", rest.strip(), {}
    if token == "DONE":
        return "done", rest.strip(), {}
    return "done", blob, {}
