import re
from typing import Any

_ORDER_ID = re.compile(r"\bORD-[0-9]+\b", re.IGNORECASE)
_CUSTOMER_ID = re.compile(r"\bCUS-[0-9]+\b", re.IGNORECASE)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def resolve_lookup_call(
    blob: str, lookups: list[str]
) -> tuple[str, dict[str, Any]] | None:
    """Pick lookup_order* tool + args when a locator appears in the customer text."""
    haystack = blob or ""
    order = _ORDER_ID.search(haystack)
    if order and "lookup_order" in lookups:
        return "lookup_order", {"order_id": order.group(0).upper()}
    customer = _CUSTOMER_ID.search(haystack)
    if customer and "lookup_order_by_customer" in lookups:
        return "lookup_order_by_customer", {"customer_id": customer.group(0).upper()}
    email = _EMAIL.search(haystack)
    if email and "lookup_order_by_email" in lookups:
        return "lookup_order_by_email", {"email": email.group(0)}
    return None


def lookup_tool_ids(tool_ids: list[str] | set[str]) -> list[str]:
    """Sorted lookup_order* ids from a hydrated tool list."""
    return sorted(name for name in tool_ids if name.startswith("lookup_order"))
