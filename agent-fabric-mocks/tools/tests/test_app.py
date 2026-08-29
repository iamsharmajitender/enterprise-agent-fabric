import json
from pathlib import Path

from fastapi.testclient import TestClient

from server import app, load_tools, match_tool, search_corpus, shopassist_customers


def _default_tools() -> list[dict]:
    return load_tools()


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_unknown_path_is_404() -> None:
    response = TestClient(app).post("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_match_is_method_and_path() -> None:
    tools = [{"id": "a", "method": "POST", "path": "/x", "response": {"ok": True}}]
    assert match_tool("POST", "/x", tools) is not None
    assert match_tool("GET", "/x", tools) is None
    assert match_tool("POST", "/y", tools) is None


def test_shopassist_lookup_variants() -> None:
    client = TestClient(app)
    rows = shopassist_customers()
    assert len(rows) >= 4
    for row in rows:
        order_id, customer_id, email = row["order_id"], row["customer_id"], row["email"]
        by_order = client.post("/shopassist/lookup_order", json={"order_id": order_id})
        by_customer = client.post(
            "/shopassist/lookup_order_by_customer", json={"customer_id": customer_id}
        )
        by_email = client.post("/shopassist/lookup_order_by_email", json={"email": email})
        for body in (by_order.json(), by_customer.json(), by_email.json()):
            assert body["order_id"] == order_id
            assert body["customer_id"] == customer_id
            assert body["email"] == email
            assert body.keys() >= {"text", "order_id", "item_id", "email"}
    policy = client.post("/shopassist/check_return_policy", json={"order_id": "ORD-22001"})
    assert policy.json()["recommended_action"] == "automatic_store_credit"


def test_default_tools_have_unique_method_and_path() -> None:
    tools = _default_tools()
    assert tools, "expected catalog/*.json"
    keys = [(str(tool["method"]).upper(), tool["path"]) for tool in tools]
    assert len(keys) == len(set(keys))
    assert "/health" not in {tool["path"] for tool in tools}
    tool_files = list(Path(__file__).resolve().parents[1].joinpath("catalog").glob("*.json"))
    assert len(tool_files) == len(tools)


def test_every_default_tool_is_served() -> None:
    tools = _default_tools()
    client = TestClient(app)
    for tool in tools:
        response = client.request(tool["method"], tool["path"], json={})
        assert response.status_code == int(tool.get("status") or 200), tool["id"]
        body = response.json()
        assert body == tool["response"], tool["id"]
        assert "text" in body, tool["id"]


def test_added_tool_is_served_without_code_change(tmp_path: Path, monkeypatch) -> None:
    tools_dir = tmp_path / "catalog"
    tools_dir.mkdir()
    (tools_dir / "account_fee_lookup.json").write_text(
        json.dumps(
            {
                "id": "account_fee_lookup",
                "method": "POST",
                "path": "/fees/explain",
                "status": 200,
                "response": {"text": "Fee of $42 is the monthly account charge."},
            }
        )
    )
    (tools_dir / "list_accounts.json").write_text(
        json.dumps(
            {
                "id": "list_accounts",
                "method": "GET",
                "path": "/accounts",
                "status": 200,
                "response": {"text": "acct-4412"},
            }
        )
    )
    monkeypatch.setenv("TOOLS_DIR", str(tools_dir))
    monkeypatch.delenv("TOOLS_JSON", raising=False)
    client = TestClient(app)
    listed = client.get("/accounts")
    assert listed.status_code == 200
    assert listed.json() == {"text": "acct-4412"}
    fee = client.post("/fees/explain", json={})
    assert fee.json()["text"].startswith("Fee of $42")


def test_corpora_search_ranks_everyday_overdraft() -> None:
    body = search_corpus(
        "fee-schedule",
        {"collection": "fee-schedule", "goal": {"utterance": "overdraft fee on Everyday account"}},
    )
    assert body["chunks"]
    assert body["chunks"][0]["id"] == "fs-everyday-od-1"
    assert "$10" in body["chunks"][0]["text"]


def test_corpora_search_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/corpora/fee-schedule/search",
        json={
            "collection": "fee-schedule",
            "goal": {"utterance": "What is the overdraft fee on our Everyday account?"},
        },
    )
    assert response.status_code == 200
    chunks = response.json()["chunks"]
    assert chunks[0]["id"] == "fs-everyday-od-1"
    disclosure = client.post(
        "/corpora/product-disclosure/search",
        json={
            "collection": "product-disclosure",
            "goal": {"utterance": "Everyday account overdraft PDS"},
        },
    )
    assert disclosure.status_code == 200
    assert disclosure.json()["chunks"][0]["id"].startswith("pd-everyday")


def test_corpora_search_unknown_corpus_is_404() -> None:
    client = TestClient(app)
    response = client.post("/corpora/missing-index/search", json={"goal": {}})
    assert response.status_code == 404


def test_tools_json_override_still_works(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "tools.json"
    config.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "id": "list_accounts",
                        "method": "GET",
                        "path": "/accounts",
                        "status": 200,
                        "response": {"text": "acct-override"},
                    }
                ]
            }
        )
    )
    monkeypatch.setenv("TOOLS_JSON", str(config))
    client = TestClient(app)
    listed = client.get("/accounts")
    assert listed.status_code == 200
    assert listed.json() == {"text": "acct-override"}
