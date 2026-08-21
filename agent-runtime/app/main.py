import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.clients import HttpCatalogueClient, HttpRegistryClient
from app.db import engine
from app.graph import build_stub_graph
from app.hydrate import HydrateError
from app.runs import RunService
from app.sql_store import SqlRunStore

WORKLOADS = frozenset({"afd", "adp", "acp", "ar", "acr"})


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def create_app(
    *,
    store: Any,
    catalogue: Any = None,
    registry: Any = None,
    graph: Any = None,
) -> FastAPI:
    app = FastAPI(title="agent-runtime")
    graph = graph if graph is not None else build_stub_graph()
    service = RunService(store, catalogue, registry, graph)
    app.state.store = store
    app.state.runs = service

    @app.middleware("http")
    async def workload_auth(request: Request, call_next):  # type: ignore[no-untyped-def]
        # FastAPI HTTP middleware: https://fastapi.tiangolo.com/tutorial/middleware/
        if request.url.path == "/health":
            return await call_next(request)
        authorization = request.headers.get("authorization")
        workload = request.headers.get("x-workload")
        if authorization != "Bearer fabric-internal" or workload not in WORKLOADS:
            return _error(401, "UNAUTHORIZED", "workload identity required")
        if workload != "afd":
            return _error(403, "FORBIDDEN", "only afd may call runtime")
        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "UP"}

    @app.post("/v1/runs")
    def start_run(body: dict[str, Any]) -> JSONResponse:
        try:
            correlation_id = service.start(body)
        except ValueError as exc:
            return _error(400, "BAD_REQUEST", str(exc))
        except HydrateError as exc:
            return _error(422, "HYDRATE_FAILED", str(exc))
        return JSONResponse(status_code=202, content={"correlation_id": correlation_id})

    @app.post("/v1/runs/{correlation_id}/turns")
    def resume_turn(correlation_id: str, body: dict[str, Any]) -> Any:
        result = service.resume(correlation_id, body)
        if result is None:
            return _error(404, "NOT_FOUND", correlation_id)
        return result

    @app.get("/v1/runs", response_model=None)
    def open_run(session_id: str) -> Any:
        if not session_id:
            return _error(400, "BAD_REQUEST", "session_id is required")
        return service.open_run(session_id)

    @app.get("/v1/runs/{correlation_id}", response_model=None)
    def run_status(correlation_id: str) -> Any:
        body = service.status(correlation_id)
        if body is None:
            return _error(404, "NOT_FOUND", correlation_id)
        return body

    return app


def build_app() -> FastAPI:
    data_plane = os.environ.get("DATA_PLANE_URL")
    registry_url = os.environ.get("REGISTRY_URL")
    return create_app(
        store=SqlRunStore(engine()),
        catalogue=HttpCatalogueClient(data_plane) if data_plane else None,
        registry=HttpRegistryClient(registry_url) if registry_url else None,
        graph=build_stub_graph(),
    )


app = build_app()
