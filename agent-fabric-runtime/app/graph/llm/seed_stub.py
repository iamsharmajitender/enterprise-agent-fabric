import json
import re
from typing import Any

from app import telemetry
from app.graph.llm.schema import dump_structured, stub_payload
from app.graph.locator import resolve_lookup_call

_TOOLS_LINE = re.compile(r"(?m)^Tools:\s*(.+)$")
_ASK_DEFAULT = (
    "Please provide an order id, customer id, or email so I can look up your order."
)
_ORDER_ID = re.compile(r"ORD-\d+")


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
                lookups = [name for name in tools if name.startswith("lookup_order")]
                if lookups:
                    if _lookup_result_in_notes(user):
                        follow_up = _shopassist_follow_up(user, tools)
                        if follow_up:
                            return follow_up
                        last = _last_prior_note(user)
                        return f"DONE {last}" if last else "DONE ok"
                    call = _lookup_call(user, lookups)
                    if call:
                        return call
                    return f"ASK {_ASK_DEFAULT}"
                if turn == 1 and tools:
                    return f"CALL {tools[0]}"
                answer = _last_prior_note(user) or "ok"
                return f"DONE {answer}"
            grounded = _prefetch_fee_answer(user)
            if grounded:
                return grounded
            return "ok"


def _shopassist_follow_up(user: str, tools: list[str]) -> str:
    """After order lookup, call billing/policy domain APIs before DONE."""
    blob = (user or "").lower()
    order_id = _order_id_from_blob(user)
    if not order_id:
        return ""
    if (
        "investigate_duplicate_charge" in tools
        and "no duplicate capture" not in blob
        and "duplicate_charge_found" not in blob
        and ("charged twice" in blob or "duplicate charge" in blob)
    ):
        payload: dict[str, str] = {"order_id": order_id}
        return "CALL investigate_duplicate_charge\n" + json.dumps(payload)
    if "check_return_policy" in tools and "policy returns" not in blob:
        payload = {"order_id": order_id, "reason": "damaged_item"}
        return "CALL check_return_policy\n" + json.dumps(payload)
    if (
        "escalate_to_human" in tools
        and "handoff_id" not in blob
        and ("escalate" in blob or "human escalation" in blob or "full refund" in blob)
    ):
        payload = {
            "order_id": order_id,
            "escalation_reason": "refund above auto limit",
        }
        return "CALL escalate_to_human\n" + json.dumps(payload)
    return ""


def _order_id_from_blob(user: str) -> str | None:
    match = _ORDER_ID.search(user or "")
    return match.group(0) if match else None


def _lookup_call(user: str, lookups: list[str]) -> str:
    """CALL the lookup that matches a locator in the user blob, or empty to ASK."""
    resolved = resolve_lookup_call(user or "", lookups)
    if resolved is None:
        return ""
    tool_id, args = resolved
    return f"CALL {tool_id}\n" + json.dumps(args)


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


def _lookup_result_in_notes(user: str) -> bool:
    """True after a lookup_order* tool appended its order summary to notes."""
    for line in (user or "").splitlines():
        if line.startswith("- Order ORD-"):
            return True
    return False


_ACCOUNT_ANSWERS = {
    "everyday": (
        "The Everyday Account overdraft fee is $10 per day when your balance is more than "
        "$10 below your approved limit, with a monthly cap of $50 [fee-schedule:fs-everyday-od-1]. "
        "Fees apply only when you have an arranged overdraft facility "
        "[product-disclosure:pd-everyday-od-1]."
    ),
    "business": (
        "The Business Account overdraft fee is $15 per day when your balance is more than "
        "$50 below your approved limit, with a monthly cap of $150 [fee-schedule:fs-business-od-1]. "
        "A business overdraft facility must be approved before scheduled fees apply "
        "[product-disclosure:pd-business-od-1]."
    ),
    "corporate": (
        "The Corporate Account overdraft fee is $25 per day when your balance is more than "
        "$500 below your approved limit, with a monthly cap of $500 [fee-schedule:fs-corporate-od-1]. "
        "Corporate overdraft fees apply to approved limits in the facility agreement "
        "[product-disclosure:pd-corporate-od-1]."
    ),
    "student": (
        "The Student Account overdraft fee is $5 per day when your balance is more than "
        "$10 below your approved limit, with a monthly cap of $25 [fee-schedule:fs-student-od-1]. "
        "The reduced student rate requires proof of full-time enrolment "
        "[product-disclosure:pd-student-od-1]."
    ),
    "premier": (
        "The Premier Account overdraft fee is waived for the first 5 days in any calendar month, "
        "then $5 per day, with a monthly cap of $75 [fee-schedule:fs-premier-od-1]. "
        "Premier customers receive five fee-free overdraft days per month "
        "[product-disclosure:pd-premier-od-1]."
    ),
}


def _prefetch_fee_answer(user: str) -> str:
    """Pattern 0 synthesis stub when prefetch chunks are present."""
    blob = (user or "").lower()
    if "packed chunks:" not in blob:
        return ""
    if "overdraft" not in blob and "fee-schedule" not in blob:
        return ""
    for account_type, answer in _ACCOUNT_ANSWERS.items():
        if account_type in blob:
            return answer
    return _ACCOUNT_ANSWERS["everyday"]

