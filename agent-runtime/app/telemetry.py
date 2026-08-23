"""OpenTelemetry setup for agent-runtime. Call setup() before creating the FastAPI app."""

from __future__ import annotations

import logging
import os
from contextvars import ContextVar, Token
from typing import Any

_LOG = logging.getLogger("fabric.events")
_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)

_state: dict[str, Any] = {"ready": False, "fastapi": None, "log_handler": None}


def fabric_resource(service_name: str) -> Any:
    """Service resource without telemetry.sdk.* (those become noisy Loki/Prometheus labels)."""
    from opentelemetry.sdk.resources import Resource

    return Resource(
        attributes={
            "service.name": service_name,
            "service.namespace": "agent-fabric",
            "deployment.environment": "local",
        }
    )


def setup() -> None:
    """Configure OTLP trace, metric, and log exporters. No-op if packages are missing."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    service_name = os.environ.get("OTEL_SERVICE_NAME", "agent-runtime")
    interval_ms = int(os.environ.get("OTEL_METRIC_EXPORT_INTERVAL", "500"))

    try:
        from opentelemetry import metrics, trace
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        _LOG.warning("opentelemetry packages missing; telemetry disabled")
        return

    resource = fabric_resource(service_name)
    base = endpoint.rstrip("/")

    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces"))
    )
    trace.set_tracer_provider(trace_provider)

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{base}/v1/metrics"),
        export_interval_millis=interval_ms,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{base}/v1/logs"))
    )
    set_logger_provider(logger_provider)
    _state["log_handler"] = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

    HTTPXClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    _state["fastapi"] = FastAPIInstrumentor
    _state["ready"] = True


def instrument_app(app: Any) -> None:
    """Attach FastAPI OpenTelemetry instrumentation once setup() has run."""
    if not _state.get("ready"):
        return
    instrumentor = _state.get("fastapi")
    if instrumentor is not None:
        instrumentor.instrument_app(app)


def bind_request_id(request_id: str | None) -> Token[str | None]:
    """Remember the inbound request id for outbound HTTP and logs."""
    return _REQUEST_ID.set(request_id if request_id else None)


def reset_request_id(token: Token[str | None]) -> None:
    """Restore the previous request id after the HTTP request ends."""
    _REQUEST_ID.reset(token)


def current_request_id() -> str | None:
    """Return the request id bound to this task, if any."""
    return _REQUEST_ID.get()


def attach(**fields: str | None) -> None:
    """Set allowlisted fields on the current span. Skips blanks. Not metric labels."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if not span.get_span_context().is_valid:
            return
        for key, value in fields.items():
            if value:
                span.set_attribute(key, value)
    except Exception:
        return


def record_error(span: Any, exc: BaseException | None = None) -> None:
    """Mark a span as failed without putting exception text on attributes."""
    try:
        from opentelemetry.trace import StatusCode

        span.set_status(StatusCode.ERROR)
        if exc is not None and hasattr(span, "record_exception"):
            span.record_exception(exc)
    except Exception:
        return


def tracer():
    """Return the runtime tracer, or a no-op if OpenTelemetry is unavailable."""
    try:
        from opentelemetry import trace

        return trace.get_tracer("agent-runtime")
    except Exception:
        return _NoopTracer()


def meter():
    """Return the runtime meter, or a no-op if OpenTelemetry is unavailable."""
    try:
        from opentelemetry import metrics

        return metrics.get_meter("agent-runtime")
    except Exception:
        return _NoopMeter()


def trace_context() -> dict[str, str]:
    """Return trace_id / span_id for logs when a valid span is current."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if not ctx.is_valid:
            return {}
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
        }
    except Exception:
        return {}


class _NoopSpan:
    def __enter__(self):
        """Stand in for a real span context manager."""
        return self

    def __exit__(self, *args):
        """Do not suppress exceptions."""
        return False

    def set_attribute(self, *args, **kwargs):
        """Ignore span attributes when telemetry is disabled."""
        return None

    def set_status(self, *args, **kwargs):
        """Ignore span status when telemetry is disabled."""
        return None

    def record_exception(self, *args, **kwargs):
        """Ignore exceptions when telemetry is disabled."""
        return None


class _NoopTracer:
    def start_as_current_span(self, name: str):
        """Return a no-op span so callers can still use `with tracer()...`."""
        return _NoopSpan()


class _NoopMeter:
    def create_counter(self, name: str):
        """Return a no-op counter when metrics are disabled."""
        return _NoopCounter()


class _NoopCounter:
    def add(self, amount: int, attributes: dict[str, str] | None = None):
        """Ignore metric increments when telemetry is disabled."""
        return None


def configure_json_logging() -> None:
    """Replace root handlers with JSON stdout (and OTLP log handler if ready)."""
    root = logging.getLogger()
    if root.handlers:
        for handler in list(root.handlers):
            root.removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)
    otel_handler = _state.get("log_handler")
    if otel_handler is not None:
        root.addHandler(otel_handler)
    root.setLevel(logging.INFO)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record as one JSON object per line."""
        import json
        from datetime import datetime, timezone

        payload: dict[str, Any] = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": os.environ.get("OTEL_SERVICE_NAME", "agent-runtime"),
        }
        payload.update(trace_context())
        request_id = current_request_id()
        if request_id:
            payload["request_id"] = request_id
        for key in (
            "event",
            "journey_id",
            "correlation_id",
            "session_id",
            "route_id",
            "route_version",
            "outcome",
            "reason_class",
            "request_id",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def emit(event: str, *, journey_id: str | None = None, **fields: str | None) -> None:
    """Write a structured business event and increment the outcome counter."""
    extra = {"event": event}
    if journey_id:
        extra["journey_id"] = journey_id
    for key, value in fields.items():
        if value is not None and value != "":
            extra[key] = value
    _LOG.info(event, extra=extra)
    try:
        counter = meter().create_counter("fabric_journey_outcome_total")
        outcome = fields.get("outcome") or event.rsplit(".", 1)[-1]
        counter.add(
            1,
            {
                "journey_id": journey_id or "unknown",
                "outcome": outcome,
                "channel": fields.get("channel") or "runtime",
            },
        )
    except Exception:
        pass
