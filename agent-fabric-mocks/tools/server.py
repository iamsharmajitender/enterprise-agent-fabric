import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import telemetry as otel

_DEFAULT_TOOLS_DIR = Path(__file__).with_name("catalog")
_DEFAULT_CORPORA_DIR = Path(__file__).with_name("data") / "corpora"
_SHOPASSIST_CUSTOMERS = Path(__file__).with_name("data") / "shopassist_customers.json"
_CORPORA_PATH = re.compile(r"^corpora/([^/]+)/search$")
_LOOKUP_NEEDLE = {
    "lookup_order": "order_id",
    "lookup_order_by_customer": "customer_id",
    "lookup_order_by_email": "email",
}


def tools_dir() -> Path:
    """Directory of per-tool JSON files (default: ./tools)."""
    return Path(os.environ.get("TOOLS_DIR", str(_DEFAULT_TOOLS_DIR)))


def corpora_dir() -> Path:
    """Directory of per-corpus JSON files (default: ./data/corpora)."""
    return Path(os.environ.get("CORPORA_DIR", str(_DEFAULT_CORPORA_DIR)))


def _corpus_file_id(corpus_id: str) -> str:
    """Map catalogue corpus ids to on-disk fixture names."""
    return corpus_id.replace("-", "_")


def load_corpora() -> dict[str, dict[str, Any]]:
    """Load corpus fixtures keyed by corpus_id."""
    directory = corpora_dir()
    if not directory.is_dir():
        return {}
    corpora: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict):
            continue
        corpus_id = str(raw.get("corpus_id") or path.stem.replace("_", "-"))
        corpora[corpus_id] = raw
    return corpora


def _goal_text(goal: dict[str, Any]) -> str:
    """Flatten goal fields into searchable text."""
    parts: list[str] = []
    for key in ("utterance", "message", "query", "topic"):
        value = goal.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    if not parts:
        parts.append(json.dumps(goal, sort_keys=True))
    return " ".join(parts).lower()


def _chunk_score(chunk: dict[str, Any], haystack: str) -> int:
    """Score a chunk by tag hits in the goal text."""
    score = 0
    tags = chunk.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            token = str(tag or "").strip().lower()
            if token and token in haystack:
                score += 2
    text = str(chunk.get("text") or "").lower()
    for token in ("overdraft", "fee", "account"):
        if token in haystack and token in text:
            score += 1
    return score


def search_corpus(corpus_id: str, request_body: dict[str, Any]) -> dict[str, Any]:
    """Return ranked chunks for a corpus search POST."""
    corpus = load_corpora().get(corpus_id)
    if corpus is None:
        return {
            "error": {
                "code": "NOT_FOUND",
                "message": f"no corpus fixture for {corpus_id!r}",
            }
        }
    raw_chunks = corpus.get("chunks")
    if not isinstance(raw_chunks, list):
        return {"chunks": []}
    goal = request_body.get("goal")
    haystack = _goal_text(goal if isinstance(goal, dict) else {})
    scored: list[tuple[int, dict[str, Any]]] = []
    for chunk in raw_chunks:
        if not isinstance(chunk, dict):
            continue
        score = _chunk_score(chunk, haystack)
        if score > 0:
            scored.append((score, chunk))
    if not scored:
        scored = [(0, chunk) for chunk in raw_chunks if isinstance(chunk, dict)]
    scored.sort(key=lambda item: item[0], reverse=True)
    limit = 4 if scored and scored[0][0] > 0 else min(3, len(scored))
    chunks = [{"id": chunk.get("id"), "text": chunk.get("text")} for _, chunk in scored[:limit]]
    return {"chunks": chunks}


def tools_json_override() -> Path | None:
    """Optional monolithic tools.json via TOOLS_JSON (tests / one-off overrides)."""
    raw = os.environ.get("TOOLS_JSON")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None


def load_tools() -> list[dict[str, Any]]:
    override = tools_json_override()
    if override is not None:
        raw = json.loads(override.read_text())
        tools = raw.get("tools") if isinstance(raw, dict) else None
        if not isinstance(tools, list):
            return []
        return [tool for tool in tools if isinstance(tool, dict)]

    directory = tools_dir()
    if not directory.is_dir():
        return []
    tools: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text())
        if isinstance(raw, dict) and "id" in raw:
            tools.append(raw)
    return _attach_shopassist_lookups(tools)


def shopassist_customers() -> list[dict[str, Any]]:
    """Dummy order / customer / email rows shared by ShopAssist lookup mocks."""
    if not _SHOPASSIST_CUSTOMERS.is_file():
        return []
    raw = json.loads(_SHOPASSIST_CUSTOMERS.read_text())
    rows = raw.get("customers") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _order_response(row: dict[str, Any]) -> dict[str, Any]:
    """Stable lookup payload so any locator on a row returns the same order."""
    price = row.get("price")
    text = (
        f"Order {row.get('order_id')}: {row.get('item_name')} ${price:g} "
        f"delivered {row.get('delivered_at')}."
    )
    return {
        "order_id": row.get("order_id"),
        "customer_id": row.get("customer_id"),
        "email": row.get("email"),
        "item_id": row.get("item_id"),
        "item_name": row.get("item_name"),
        "price": price,
        "delivered_at": row.get("delivered_at"),
        "text": text,
    }


def _attach_shopassist_lookups(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fill lookup_order* defaults and body_contains variants from the shared fixture."""
    rows = shopassist_customers()
    if not rows:
        return tools
    default = _order_response(rows[0])
    for tool in tools:
        field = _LOOKUP_NEEDLE.get(str(tool.get("id") or ""))
        if not field:
            continue
        tool["response"] = default
        tool["match"] = [
            {"body_contains": str(row.get(field) or ""), "response": _order_response(row)}
            for row in rows
            if row.get(field)
        ]
    return tools


def match_tool(method: str, path: str, tools: list[dict[str, Any]]) -> dict[str, Any] | None:
    want_method = method.upper()
    for tool in tools:
        tool_method = str(tool.get("method") or "POST").upper()
        tool_path = str(tool.get("path") or "")
        if tool_method == want_method and tool_path == path:
            return tool
    return None


def resolve_response(tool: dict[str, Any], request_body: dict[str, Any]) -> dict[str, Any]:
    """Pick default or body-matched variant response (first match wins)."""
    default = tool.get("response")
    if not isinstance(default, dict):
        default = {}
    haystack = json.dumps(request_body, sort_keys=True).lower()
    variants = tool.get("match")
    if not isinstance(variants, list):
        return default
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        needle = str(variant.get("body_contains") or "").strip().lower()
        if not needle or needle not in haystack:
            continue
        body = variant.get("response")
        return body if isinstance(body, dict) else default
    return default


app = FastAPI(title="agent-mocks")
otel.setup()
otel.quiet_framework_loggers()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP"}


async def _request_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return body if isinstance(body, dict) else {}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def dispatch(request: Request, path: str) -> JSONResponse:
    corpora_match = _CORPORA_PATH.match(path)
    if corpora_match is not None and request.method.upper() == "POST":
        corpus_id = corpora_match.group(1)
        body = search_corpus(corpus_id, await _request_body(request))
        if "error" in body:
            return JSONResponse(status_code=404, content=body)
        return JSONResponse(status_code=200, content=body)

    route = "/" + path
    tool = match_tool(request.method, route, load_tools())
    if tool is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"no mock for {request.method} {route}",
                }
            },
        )
    request_body = await _request_body(request)
    body = resolve_response(tool, request_body)
    status = int(tool.get("status") or 200)
    return JSONResponse(status_code=status, content=body)


otel.instrument_app(app)
