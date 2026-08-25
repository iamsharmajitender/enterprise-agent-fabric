import json
from pathlib import Path

from fastapi.testclient import TestClient

from server import app, load_tools, match_tool


def _default_tools() -> list[dict]:
    return load_tools()


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_fee_lookup_from_default_config() -> None:
    response = TestClient(app).post("/fees/explain", json={"utterance": "Why was I charged $42?"})
    assert response.status_code == 200
    assert response.json() == {"text": "Fee of $42 is the monthly account charge."}


def test_claims_adjudicate_tools_from_default_config() -> None:
    client = TestClient(app)
    playbook = client.post("/legal/playbook/search", json={"query": "water damage"})
    clauses = client.post("/legal/clauses/search", json={"query": "exclusion 4.2"})
    risk = client.post("/legal/risk", json={"score_profile": "claims"})
    memo = client.post("/legal/memo", json={"audience": "claims-ops"})
    assert playbook.status_code == 200
    assert clauses.status_code == 200
    assert risk.status_code == 200
    assert memo.status_code == 200
    assert playbook.json()["text"].startswith("Playbook:")
    assert clauses.json()["text"].startswith("Clause 4.2:")
    assert "Risk score" in risk.json()["text"]
    assert memo.json() == {"text": "Deny claim: exclusion 4.2 applies; notice was late."}


def test_unknown_path_is_404() -> None:
    response = TestClient(app).post("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_match_is_method_and_path() -> None:
    tools = [{"id": "a", "method": "POST", "path": "/x", "response": {"ok": True}}]
    assert match_tool("POST", "/x", tools) is not None
    assert match_tool("GET", "/x", tools) is None
    assert match_tool("POST", "/y", tools) is None


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
