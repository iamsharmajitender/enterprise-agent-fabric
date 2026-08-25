import json
import logging

from app import telemetry


def test_fabric_resource_omits_sdk_labels() -> None:
    try:
        resource = telemetry.fabric_resource("agent-runtime")
    except ImportError:
        return
    keys = set(resource.attributes)
    assert "telemetry.sdk.language" not in keys
    assert "telemetry.sdk.name" not in keys
    assert "telemetry.sdk.version" not in keys
    assert resource.attributes["service.name"] == "agent-runtime"


def test_json_formatter_includes_request_id() -> None:
    token = telemetry.bind_request_id("req-edge-1")
    try:
        formatter = telemetry._JsonFormatter()
        record = logging.LogRecord(
            name="fabric.events",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="run.started",
            args=(),
            exc_info=None,
        )
        record.event = "run.started"
        record.correlation_id = "corr-abc"
        payload = json.loads(formatter.format(record))
        assert payload["request_id"] == "req-edge-1"
        assert payload["correlation_id"] == "corr-abc"
        assert payload["event"] == "run.started"
        assert "trace_id" not in payload
    finally:
        telemetry.reset_request_id(token)


def test_attach_is_noop_without_span() -> None:
    telemetry.attach(session_id="sess-88", correlation_id="corr-9f3c")
