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


def test_json_formatter_includes_stage_fields() -> None:
    formatter = telemetry._JsonFormatter()
    record = logging.LogRecord(
        name="fabric.events",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="run.stage.completed",
        args=(),
        exc_info=None,
    )
    record.event = "run.stage.completed"
    record.stage_id = "account_fee_lookup"
    record.latency_ms = "12"
    record.request_digest = "sha256:abc"
    record.response_digest = "sha256:def"
    payload = json.loads(formatter.format(record))
    assert payload["stage_id"] == "account_fee_lookup"
    assert payload["latency_ms"] == "12"


def test_emit_stage_started_and_completed() -> None:
    token = telemetry.bind_run_event_context(
        journey_id="chat.fee_explain",
        correlation_id="corr-1",
        session_id="chat-abc",
        route_id="fee_explain",
        route_version="2026.08.1",
        channel="web",
        ingress="chat",
    )
    try:
        telemetry.emit_stage_started("lookup", "none", {"account_id": "a1"})
        latency = telemetry.emit_stage_completed("lookup", {"fee": 1}, llm_role="none")
        assert latency >= 0
    finally:
        telemetry.reset_run_event_context(token)


def test_emit_llm_started_and_completed() -> None:
    token = telemetry.bind_run_event_context(
        journey_id="chat.pattern1_case",
        correlation_id="corr-2",
        session_id="chat-xyz",
        route_id="pattern1_case",
        route_version="2026.08.1",
        channel="web",
        ingress="chat",
    )
    llm_token = telemetry.bind_llm_call_context(stage_id="agent_decision", llm_role="agent")
    try:
        telemetry.emit_llm_started(
            "system prompt",
            "user blob",
            structured=True,
            schema_name="AgentDecision",
            llm_model="seed-stub",
        )
        telemetry.emit_llm_completed(
            {"action": "done", "message": "ok"},
            latency_ms=42,
            llm_model="seed-stub",
        )
    finally:
        telemetry.reset_llm_call_context(llm_token)
        telemetry.reset_run_event_context(token)


def test_json_formatter_includes_llm_fields() -> None:
    formatter = telemetry._JsonFormatter()
    record = logging.LogRecord(
        name="fabric.events",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="run.llm.completed",
        args=(),
        exc_info=None,
    )
    record.event = "run.llm.completed"
    record.stage_id = "agent_decision"
    record.llm_role = "agent"
    record.llm_model = "seed-stub"
    record.llm_schema = "AgentDecision"
    record.latency_ms = "15"
    record.request_digest = "sha256:abc"
    record.response_digest = "sha256:def"
    record.llm_messages = '[{"role":"system","content":"sys"},{"role":"user","content":"usr"}]'
    payload = json.loads(formatter.format(record))
    assert payload["stage_id"] == "agent_decision"
    assert payload["llm_model"] == "seed-stub"
    assert payload["llm_schema"] == "AgentDecision"
    assert "system" in payload["llm_messages"]


def test_stage_payloads_enabled() -> None:
    import os

    prev = os.environ.get("FABRIC_LOG_STAGE_PAYLOADS")
    os.environ["FABRIC_LOG_STAGE_PAYLOADS"] = "1"
    try:
        assert telemetry.stage_payloads_enabled()
    finally:
        if prev is None:
            os.environ.pop("FABRIC_LOG_STAGE_PAYLOADS", None)
        else:
            os.environ["FABRIC_LOG_STAGE_PAYLOADS"] = prev


def test_json_formatter_includes_request_id() -> None:
    token = telemetry.bind_request_id("req-edge-1")
    try:
        formatter = telemetry._JsonFormatter()
        record = logging.LogRecord(
            name="fabric.events",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="run.graph.started",
            args=(),
            exc_info=None,
        )
        record.event = "run.graph.started"
        record.correlation_id = "corr-abc"
        payload = json.loads(formatter.format(record))
        assert payload["request_id"] == "req-edge-1"
        assert payload["correlation_id"] == "corr-abc"
        assert payload["event"] == "run.graph.started"
        assert "trace_id" not in payload
    finally:
        telemetry.reset_request_id(token)


def test_attach_is_noop_without_span() -> None:
    telemetry.attach(session_id="sess-88", correlation_id="corr-9f3c")


def test_configure_json_logging_sends_otel_only_for_fabric_events() -> None:
    sentinel = logging.Handler()
    telemetry._state["log_handler"] = sentinel
    try:
        telemetry.configure_json_logging()
        root = logging.getLogger()
        events = logging.getLogger("fabric.events")
        assert sentinel not in root.handlers
        assert sentinel in events.handlers
        assert logging.getLogger("httpx").level == logging.WARNING
    finally:
        telemetry._state["log_handler"] = None
        events = logging.getLogger("fabric.events")
        if sentinel in events.handlers:
            events.removeHandler(sentinel)
