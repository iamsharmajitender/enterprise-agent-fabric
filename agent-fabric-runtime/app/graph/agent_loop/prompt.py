import json
from typing import Any

from app.graph.payload import schema_required

ASK_DEFAULT = "Please provide the information needed to continue."

_ENTERPRISE_RULES = """
You are an enterprise AI agent. Choose exactly one action per turn: tool_call, ask, or done.

Identifier rules (highest priority):

- Never invent order_id, customer_id, account_id, or any locator. Copy only from goal text, a customer: note, or prior stage output fields.
- If a tool needs an identifier that is not in goal or prior stage outputs, use ask — not tool_call.
- If prior stage outputs include a note starting with `customer:`, treat it as the customer's reply.
- If prior stage outputs include a note starting with `ask:`, the run is waiting for that customer reply — do not tool_call until a `customer:` note follows.
- If prior stage outputs already include a completed note for a tool (e.g. lookup_order_by_order_id: order_id=...), do not tool_call that tool again unless the customer supplied new information.

Tool rules:

- Only use registered tools. tool_call arguments must match input_schema.
- When prior stage outputs include `item_id=`, use that exact value later — never substitute a product name.
- When prior stage outputs include `recommended_action=escalate_to_human`, tool_call escalate_to_human next.
- After prior stage outputs include `handoff_id=`, use done — never escalate again.
- Do not fabricate tool results.
""".strip()


def _tool_lines(tools: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for tool in tools:
        tool_id = str(tool.get("id") or "").strip()
        if not tool_id:
            continue
        description = str(tool.get("description") or "").strip()
        lines.append(f"- {tool_id}: {description}")
    return "\n".join(lines) if lines else "- (none)"


def tool_schema_block(tools: list[dict[str, Any]]) -> str:
    """Declare required tool args for the seed stub and provider prompts."""
    lines: list[str] = []
    for tool in tools:
        tool_id = str(tool.get("id") or "")
        schema = tool.get("input_schema")
        if not tool_id or not isinstance(schema, dict) or not schema_required(schema):
            continue
        lines.append(f"- {tool_id}: {json.dumps(schema, separators=(',', ':'))}")
    if not lines:
        return ""
    return "Tool input schemas:\n" + "\n".join(lines)


def build_agent_prompt(tools: list[dict[str, Any]], host_prompt: str = "") -> str:
    """Compose the Pattern 1 system prompt from host text, enterprise rules, and tools."""
    sections = []
    extra = (host_prompt or "").strip()
    if extra:
        sections.append(extra)
    sections.append(_ENTERPRISE_RULES)
    sections.append(f"Available tools:\n\n{_tool_lines(tools)}")
    schema_block = tool_schema_block(tools)
    if schema_block:
        sections.append(schema_block)
    return "\n\n".join(sections)
