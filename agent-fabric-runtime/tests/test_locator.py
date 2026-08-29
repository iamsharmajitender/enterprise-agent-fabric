from app.graph.locator import resolve_lookup_call


def test_resolve_lookup_call_prefers_order_id() -> None:
    lookups = ["lookup_order", "lookup_order_by_customer", "lookup_order_by_email"]
    blob = "customer: CUS-4412\nnotes: ORD-55210"
    assert resolve_lookup_call(blob, lookups) == ("lookup_order", {"order_id": "ORD-55210"})


def test_resolve_lookup_call_by_customer() -> None:
    lookups = ["lookup_order_by_customer", "lookup_order_by_email"]
    assert resolve_lookup_call("customer: CUS-4412", lookups) == (
        "lookup_order_by_customer",
        {"customer_id": "CUS-4412"},
    )


def test_resolve_lookup_call_by_email() -> None:
    lookups = ["lookup_order_by_email"]
    assert resolve_lookup_call("jane.doe@shopassist.example", lookups) == (
        "lookup_order_by_email",
        {"email": "jane.doe@shopassist.example"},
    )
