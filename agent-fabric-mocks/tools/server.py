import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import telemetry as otel

_DEFAULT_TOOLS_DIR = Path(__file__).with_name("catalog")


def tools_dir() -> Path:
    """Directory of per-tool JSON files (default: ./tools)."""
    return Path(os.environ.get("TOOLS_DIR", str(_DEFAULT_TOOLS_DIR)))


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
    return tools


def match_tool(method: str, path: str, tools: list[dict[str, Any]]) -> dict[str, Any] | None:
    want_method = method.upper()
    for tool in tools:
        tool_method = str(tool.get("method") or "POST").upper()
        tool_path = str(tool.get("path") or "")
        if tool_method == want_method and tool_path == path:
            return tool
    return None


app = FastAPI(title="tool-mock")
otel.setup()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def dispatch(request: Request, path: str) -> JSONResponse:
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
    body = tool.get("response")
    if not isinstance(body, dict):
        body = {}
    status = int(tool.get("status") or 200)
    return JSONResponse(status_code=status, content=body)


otel.instrument_app(app)
