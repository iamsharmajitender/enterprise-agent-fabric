from typing import Any

from app.core.agent_core import RunService
from app.core.execution import run_loop
from app.core.state import RunPin
from app.graph.subagent_gate import (
    SubagentWaiting,
    join_enabled,
    merge_subagent_packet,
    parse_subagent_packet,
    poll_subagents,
)
from app.graph.workflow import build_tool_graph
from tests.in_memory_store import InMemoryRunStore


class _CapturingSpan:
    def __init__(self) -> None:
        self.attributes: dict[str, Any] = {}
        self.status: Any = None
        self.exceptions: list[BaseException] = []

    def __enter__(self) -> "_CapturingSpan":
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_status(self, status: Any) -> None:
        self.status = status

    def record_exception(self, exc: BaseException) -> None:
        self.exceptions.append(exc)


class _CapturingTracer:
    def __init__(self) -> None:
        self.span = _CapturingSpan()

    def start_as_current_span(self, name: str) -> _CapturingSpan:
        return self.span


def test_join_enabled_from_invoke_or_pinned() -> None:
    assert join_enabled({}, {"join": True}) is True
    assert join_enabled({"join": True}, {}) is True
    assert join_enabled({}, {}) is False


def test_parse_subagent_packet_requires_terminal_rows() -> None:
    assert parse_subagent_packet({}) is None
    assert parse_subagent_packet({"decision": "approve"}) is None
    assert parse_subagent_packet(
        {"subagents": [{"correlation_id": "c1", "status": "running"}]}
    ) is None
    packet = parse_subagent_packet(
        {
            "subagents": [
                {"correlation_id": "c1", "status": "completed", "result": {"ok": True}}
            ]
        }
    )
    assert packet == [
        {"correlation_id": "c1", "status": "completed", "result": {"ok": True}}
    ]


def test_join_note_includes_draft_text() -> None:
    from app.graph.subagent_gate import join_note, subagent_result_text

    assert (
        subagent_result_text(
            {"message": "Dear customer…"}, status="completed", stage_id="draft_reply"
        )
        == "Dear customer…"
    )
    note = join_note(
        "draft_reply",
        [
            {
                "correlation_id": "corr-1",
                "status": "completed",
                "result": {"message": "Dear customer, we are reviewing ORD-77819."},
            }
        ],
    )
    assert "Dear customer, we are reviewing ORD-77819." in note
    assert "['completed']" not in note


def test_merge_subagent_packet_into_stage_slot() -> None:
    slots = {
        "start_contract_review": {
            "route_id": "contract_review",
            "correlation_id": "corr-s1",
            "status": "running",
            "payload": {"order_id": "ORD-1"},
        }
    }
    merged = merge_subagent_packet(
        slots,
        "start_contract_review",
        [{"correlation_id": "corr-s1", "status": "completed", "result": {"flags": ["damage"]}}],
    )
    assert merged["start_contract_review"]["status"] == "completed"
    assert merged["start_contract_review"]["result"] == {"flags": ["damage"]}
    assert merged["start_contract_review"]["payload"] == {"order_id": "ORD-1"}


def test_poll_subagents_waits_until_completed() -> None:
    ticks = {"n": 0}

    class FakeJobs:
        def status(self, correlation_id: str) -> dict[str, Any]:
            ticks["n"] += 1
            if ticks["n"] < 2:
                return {"correlation_id": correlation_id, "status": "running"}
            return {
                "correlation_id": correlation_id,
                "status": "completed",
                "result": {"message": "done"},
            }

    out = poll_subagents(FakeJobs(), ["corr-a"], interval_s=0.01, timeout_s=2)
    assert out == [
        {"correlation_id": "corr-a", "status": "completed", "result": {"message": "done"}}
    ]


def test_agent_kind_join_pauses_then_resumes(store: InMemoryRunStore) -> None:
    starts: list[str] = []

    class FakeJobs:
        def start(self, route_id: str, *_args, **_kwargs) -> dict[str, Any]:
            starts.append(route_id)
            return {"correlation_id": "corr-sub-1"}

        def status(self, correlation_id: str) -> dict[str, Any]:
            return {
                "correlation_id": correlation_id,
                "status": "completed",
                "result": {"message": "order ok", "flags": ["damage_claim"]},
            }

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            return {"text": f"http:{invoke.get('url')}"}

    class Llm:
        def complete(self, system: str, user: str, schema=None) -> str:
            return "Case closed with subagent findings."

    tools = [
        {
            "id": "start_contract_review",
            "kind": "agent",
            "join": True,
            "input_schema": {
                "type": "object",
                "required": ["document_id"],
                "properties": {"document_id": {"type": "string"}},
            },
            "invoke": {
                "method": "POST",
                "url": "https://api-afd.internal/v1/jobs",
                "body": {"route_id": "contract_review"},
                "join": True,
            },
        },
        {
            "id": "respond",
            "llm_role": "synthesis",
            "invoke": {},
        },
    ]
    profile = {"working": "session", "loop": "checkpoint"}
    pin = RunPin(
        correlation_id="corr-parent-join",
        idempotency_key="job-parent-join",
        session_id="job:fraud",
        route_id="fraud_investigate",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=tools,
        status="running",
    )
    store.insert(pin)
    paused = run_loop(
        build_tool_graph(tools, Invoker(), llm=Llm(), jobs=FakeJobs()),
        store,
        pin,
        goal={"document_id": "doc-77819"},
        profile=profile,
    )
    assert paused.status == "waiting"
    assert paused.checkpoint["waiting_for"] == "subagent"
    assert paused.checkpoint["subagent_ids"] == ["corr-sub-1"]
    assert starts == ["contract_review"]

    class FakeCatalogue:
        def get_route(self, *_a, **_k):
            return {
                "route_id": "fraud_investigate",
                "route_version": "2026.08.1",
                "autonomy_mode": 2,
                "memory_profile": profile,
            }

        def get_prompt(self, *_a, **_k):
            return {}

    class FakeRegistry:
        pass

    service = RunService(
        store,
        FakeCatalogue(),
        FakeRegistry(),
        invoker=Invoker(),
        llm=Llm(),
        jobs=FakeJobs(),
        schedule_run=lambda fn: None,
    )

    def graph_for(hydrated_tools, **kwargs):  # type: ignore[no-untyped-def]
        return build_tool_graph(
            tools,
            Invoker(),
            llm=Llm(),
            jobs=FakeJobs(),
            start_index=kwargs.get("start_index", 0),
        )

    service._graph_for = graph_for  # type: ignore[method-assign]
    emitted: list[dict] = []

    def capture(event: dict) -> None:
        emitted.append(event)

    import app.core.agent_core as agent_core_mod

    original = agent_core_mod.emit_async
    agent_core_mod.emit_async = capture  # type: ignore[assignment]
    try:
        body = service.resume(
            "corr-parent-join",
            {
                "subagents": [
                    {
                        "correlation_id": "corr-sub-1",
                        "status": "completed",
                        "result": {"message": "order ok", "flags": ["damage_claim"]},
                    }
                ]
            },
        )
    finally:
        agent_core_mod.emit_async = original  # type: ignore[assignment]
    assert body is not None
    assert body["status"] == "completed"
    updated = store.get("corr-parent-join")
    assert updated is not None
    slots = (updated.working or {}).get("slots") or {}
    # working may be cleared after complete — check notes/result instead
    assert "Case closed" in str((updated.result or {}).get("message") or "")
    terminals = [e for e in emitted if e.get("event_type") == "run.terminal"]
    assert terminals, "resume must emit run.terminal so audit leaves in_progress"
    assert terminals[-1].get("payload", {}).get("status") == "completed"


def test_agent_kind_join_raises_subagent_waiting() -> None:
    class FakeJobs:
        def start(self, *_a, **_k) -> dict[str, Any]:
            return {"correlation_id": "corr-x"}

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("no domain HTTP")

    graph = build_tool_graph(
        [
            {
                "id": "start_kyc_onboarding",
                "kind": "agent",
                "join": True,
                "input_schema": {
                    "type": "object",
                    "required": ["applicant_id"],
                    "properties": {"applicant_id": {"type": "string"}},
                },
                "invoke": {
                    "body": {"route_id": "kyc_onboarding"},
                    "join": True,
                },
            }
        ],
        Invoker(),
        jobs=FakeJobs(),
    )
    try:
        graph.invoke(
            {
                "result": "",
                "goal": {"applicant_id": "kyc-1"},
                "notes": [],
                "slots": {},
                "correlation_id": "corr-parent",
            }
        )
    except SubagentWaiting as exc:
        assert exc.subagent_ids == ["corr-x"]
        assert exc.stage_id == "start_kyc_onboarding"
        assert exc.state["slots"]["start_kyc_onboarding"]["status"] == "running"
        return
    raise AssertionError("expected SubagentWaiting")


def test_subagent_waiting_is_not_a_span_error(monkeypatch, store: InMemoryRunStore) -> None:
    """Join pause is control flow. Tempo must not show exception.message for it."""
    tracer = _CapturingTracer()
    monkeypatch.setattr("app.core.execution.telemetry.tracer", lambda: tracer)

    class FakeJobs:
        def start(self, *_a, **_k) -> dict[str, Any]:
            return {"correlation_id": "corr-779588350e75"}

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise AssertionError("no domain HTTP")

    tools = [
        {
            "id": "start_contract_review",
            "kind": "agent",
            "join": True,
            "input_schema": {
                "type": "object",
                "required": ["document_id"],
                "properties": {"document_id": {"type": "string"}},
            },
            "invoke": {
                "body": {"route_id": "contract_review"},
                "join": True,
            },
        }
    ]
    pin = RunPin(
        correlation_id="corr-parent-wait",
        idempotency_key="job-parent-wait",
        session_id="job:fraud",
        route_id="fraud_investigate",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=tools,
        status="running",
    )
    store.insert(pin)
    paused = run_loop(
        build_tool_graph(tools, Invoker(), jobs=FakeJobs()),
        store,
        pin,
        goal={"document_id": "doc-77819"},
        profile={"working": "session", "loop": "checkpoint"},
    )
    assert paused.status == "waiting"
    assert paused.checkpoint["waiting_for"] == "subagent"
    assert tracer.span.exceptions == []
    assert tracer.span.status is None
    assert tracer.span.attributes["waiting_for"] == "subagent"
    assert tracer.span.attributes["stage_id"] == "start_contract_review"
    assert tracer.span.attributes["subagent_ids"] == "corr-779588350e75"
