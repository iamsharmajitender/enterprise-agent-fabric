from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.agents.hydrate import HydrateError
from app.api.errors import error_response

router = APIRouter()


@router.post("/v1/runs")
def start_run(request: Request, body: dict[str, Any]) -> JSONResponse:
    """Start a new run: hydrate and pin before 202; graph runs asynchronously."""
    try:
        correlation_id = request.app.state.runs.start(body)
    except ValueError as exc:
        return error_response(400, "BAD_REQUEST", str(exc))
    except HydrateError as exc:
        return error_response(422, "HYDRATE_FAILED", str(exc))
    return JSONResponse(status_code=202, content={"correlation_id": correlation_id})


@router.post("/v1/runs/{correlation_id}/turns")
def resume_turn(request: Request, correlation_id: str, body: dict[str, Any]) -> Any:
    """Continue an existing run with a follow-up turn payload."""
    try:
        result = request.app.state.runs.resume(correlation_id, body)
    except ValueError as exc:
        return error_response(400, "BAD_REQUEST", str(exc))
    if result is None:
        return error_response(404, "NOT_FOUND", correlation_id)
    return result


@router.get("/v1/runs", response_model=None)
def open_run(request: Request, session_id: str) -> Any:
    """Look up the latest run for a session id."""
    if not session_id:
        return error_response(400, "BAD_REQUEST", "session_id is required")
    return request.app.state.runs.open_run(session_id)


@router.get("/v1/runs/{correlation_id}", response_model=None)
def run_status(request: Request, correlation_id: str) -> Any:
    """Return slim status (and result, if complete) for a correlation id."""
    body = request.app.state.runs.status(correlation_id)
    if body is None:
        return error_response(404, "NOT_FOUND", correlation_id)
    return body
