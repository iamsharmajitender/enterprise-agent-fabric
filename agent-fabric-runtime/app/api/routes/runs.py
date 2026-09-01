"""HTTP surface for Agent Runtime runs.

Thin adapters: validate/translate HTTP, then call RunService.
Business lifecycle lives in app.core.agent_core — not here.
"""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.agents.hydrate import HydrateError
from app.api.errors import error_response

router = APIRouter()


@router.post("/v1/runs")
def start_run(request: Request, body: dict[str, Any]) -> JSONResponse:
    """Start a new run: hydrate + pin before 202; graph continues asynchronously.

    request.app.state.runs is a RunService attached in create_app / build_app.
    (IDE may not resolve .start — app.state is untyped Starlette State.)
    """
    try:
        correlation_id = request.app.state.runs.start(body)
    except ValueError as exc:
        return error_response(400, "BAD_REQUEST", str(exc))
    except HydrateError as exc:
        return error_response(422, "HYDRATE_FAILED", str(exc))
    # 202: accepted for processing — pin is durable; graph may still be running.
    return JSONResponse(status_code=202, content={"correlation_id": correlation_id})


@router.post("/v1/runs/{correlation_id}/turns")
def resume_turn(request: Request, correlation_id: str, body: dict[str, Any]) -> Any:
    """Continue an existing run (gate packet, customer reply, or follow-up goal)."""
    try:
        result = request.app.state.runs.resume(correlation_id, body)
    except ValueError as exc:
        return error_response(400, "BAD_REQUEST", str(exc))
    if result is None:
        return error_response(404, "NOT_FOUND", correlation_id)
    return result


@router.get("/v1/runs", response_model=None)
def open_run(request: Request, session_id: str) -> Any:
    """Look up the latest run for a chat/job session id."""
    if not session_id:
        return error_response(400, "BAD_REQUEST", "session_id is required")
    return request.app.state.runs.open_run(session_id)


@router.get("/v1/runs/{correlation_id}", response_model=None)
def run_status(request: Request, correlation_id: str) -> Any:
    """Slim status (and result when complete) for polling clients."""
    body = request.app.state.runs.status(correlation_id)
    if body is None:
        return error_response(404, "NOT_FOUND", correlation_id)
    return body
