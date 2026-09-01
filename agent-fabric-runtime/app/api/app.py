"""FastAPI application factory for Agent Runtime (AR).

``app`` is the module-level FastAPI instance uvicorn loads via ``app.main:app``.
``create_app`` injects dependencies for tests; ``build_app`` wires production
clients from environment variables and is invoked once at import time.
"""
import os
from typing import Any

from fastapi import FastAPI, Request

from app import telemetry
from app.agents.clients import HttpCatalogueClient, HttpRegistryClient
from app.agents.jobs_client import HttpJobsClient
from app.agents.prefetch_client import HttpPrefetchClient
from app.api.errors import error_response
from app.api.routes.health import router as health_router
from app.api.routes.runs import router as runs_router
from app.core.agent_core import RunService, run_in_background, run_inline
from app.core.db import engine
from app.core.run_store import PersistentRunStore
from app.graph.llm import llm_from_env
from app.tools.invoker import HttpToolClient

# Known fabric workload identities (X-Workload header). Only AFD may start runs.
WORKLOADS = frozenset({"afd", "adp", "acp", "ar", "acr"})

app = FastAPI(title="agent-runtime")


@app.middleware("http")
async def workload_auth(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Reject calls that are not from Front Door; /health stays open."""
    if request.url.path == "/health":
        return await call_next(request)
    authorization = request.headers.get("authorization")
    workload = request.headers.get("x-workload")
    if authorization != "Bearer fabric-internal" or workload not in WORKLOADS:
        return error_response(401, "UNAUTHORIZED", "workload identity required")
    # Channels reach AR only through AFD freeze/start; sibling services must not dial runs.
    if workload != "afd":
        return error_response(403, "FORBIDDEN", "only afd may call runtime")
    return await call_next(request)


@app.middleware("http")
async def inbound_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Copy X-Request-Id onto the server span and outbound client calls (outermost)."""
    token = telemetry.bind_request_id(request.headers.get("x-request-id"))
    try:
        telemetry.attach(request_id=request.headers.get("x-request-id"))
        return await call_next(request)
    finally:
        telemetry.reset_request_id(token)


app.include_router(health_router)
app.include_router(runs_router)


def create_app(
    *,
    store: Any,
    catalogue: Any = None,
    registry: Any = None,
    graph: Any = None,
    tool_invoker: Any = None,
    llm: Any = None,
    prefetch: Any = None,
    jobs: Any = None,
    schedule_run: Any = None,
) -> FastAPI:
    """Attach run dependencies (store, catalogue, tools, LLM) onto the app.

    Mutates the shared module-level ``app`` instance (same object uvicorn serves).
    ``schedule_run`` defaults to inline execution so TestClient callers see
    completion on the same thread. Production ``build_app`` uses a background thread.
    """
    app.state.store = store
    app.state.runs = RunService(
        store,
        catalogue,
        registry,
        graph=graph,
        invoker=tool_invoker,
        llm=llm,
        prefetch=prefetch,
        jobs=jobs,
        schedule_run=schedule_run if schedule_run is not None else run_inline,
    )
    telemetry.instrument_app(app)
    return app


def build_app() -> FastAPI:
    """Wire production clients and telemetry, then return the FastAPI app."""
    telemetry.setup()
    telemetry.configure_json_logging()
    data_plane = os.environ.get("DATA_PLANE_URL")
    registry_url = os.environ.get("REGISTRY_URL")
    return create_app(
        store=PersistentRunStore(engine()),
        # Optional in local tests; hydrate/pin fail fast if catalogue or registry is missing.
        catalogue=HttpCatalogueClient(data_plane) if data_plane else None,
        registry=HttpRegistryClient(registry_url) if registry_url else None,
        tool_invoker=HttpToolClient(),
        llm=llm_from_env(),
        prefetch=HttpPrefetchClient(),
        jobs=HttpJobsClient(),
        schedule_run=run_in_background,
    )


# Eager init so ``uvicorn app.main:app`` serves a fully wired app without a factory arg.
build_app()
