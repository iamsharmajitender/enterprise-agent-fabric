"""Optional OpenTelemetry for tool-mock. No-op unless OTEL_EXPORTER_OTLP_ENDPOINT is set."""

from __future__ import annotations

import os
from typing import Any

_state: dict[str, Any] = {"ready": False, "fastapi": None}


def setup() -> None:
    """Export traces to OTLP when Compose (or a host) sets the exporter endpoint."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return

    service_name = os.environ.get("OTEL_SERVICE_NAME", "tool-mock")
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.namespace": "agent-fabric",
            "deployment.environment": "local",
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces"))
    )
    trace.set_tracer_provider(provider)
    _state["fastapi"] = FastAPIInstrumentor
    _state["ready"] = True


def instrument_app(app: Any) -> None:
    """Attach FastAPI instrumentation after routes exist."""
    if not _state.get("ready"):
        return
    instrumentor = _state.get("fastapi")
    if instrumentor is not None:
        instrumentor.instrument_app(app)
