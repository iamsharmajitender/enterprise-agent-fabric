import json
import re

from fastapi.testclient import TestClient

from app.core.agent_core import RunService
from app.core.execution import run_loop
from app.core.memory import persist_stage
from app.core.state import RunPin
from app.graph.workflow import build_agent_loop, build_tool_graph
from tests.llm_fakes import TextLlm
from app.main import create_app
from tests.conftest import (
    AFD,
    CANNED,
    START_BODY,
    FakeCatalogue,
    FakeInvoker,
    FakeLlm,
    FakeRegistry,
)


def test_first_start_returns_202_with_correlation_id(client: TestClient) -> None:
    response = client.post("/v1/runs", headers=AFD, json=START_BODY)
    assert response.status_code == 202
    body = response.json()
    assert set(body.keys()) == {"correlation_id"}
    corr = body["correlation_id"]
    assert corr.startswith("corr-")
    # corr- + standard UUID (8-4-4-4-12 hex)
    assert re.fullmatch(
        r"corr-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        corr,
    )
    assert "route_id" not in body


def test_same_idempotency_key_returns_original_id_one_row(
    client: TestClient, store, catalogue: FakeCatalogue
) -> None:
    first = client.post("/v1/runs", headers=AFD, json=START_BODY)
    second = client.post("/v1/runs", headers=AFD, json=START_BODY)
    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["correlation_id"] == second.json()["correlation_id"]
    assert len(store.all()) == 1
    assert len(catalogue.route_calls) == 1


def test_channel_bearer_is_401(client: TestClient) -> None:
    response = client.post(
        "/v1/runs",
        headers={"Authorization": "Bearer stub", "X-Stub-Claims": json.dumps({"sub": "jane"})},
        json=START_BODY,
    )
    assert response.status_code == 401
    assert "correlation_id" not in response.json()


def test_missing_auth_is_401(client: TestClient) -> None:
    response = client.post("/v1/runs", json=START_BODY)
    assert response.status_code == 401


def test_non_afd_workload_is_403(client: TestClient) -> None:
    response = client.post(
        "/v1/runs",
        headers={"Authorization": "Bearer fabric-internal", "X-Workload": "ar"},
        json=START_BODY,
    )
    assert response.status_code == 403
    assert "correlation_id" not in response.json()


def test_successful_start_writes_hydrated_tools(client: TestClient, store) -> None:
    response = client.post("/v1/runs", headers=AFD, json=START_BODY)
    assert response.status_code == 202
    pin = store.get(response.json()["correlation_id"])
    assert pin is not None
    assert pin.hydrated_tools
    assert pin.hydrated_tools[0]["id"] == "fetch_record"
    assert pin.hydrated_tools[0]["invoke"]["url"] == "http://agent-mocks:3010/tools/fetch"


def test_catalogue_get_uses_pinned_version_never_active(
    client: TestClient, catalogue: FakeCatalogue
) -> None:
    client.post("/v1/runs", headers=AFD, json=START_BODY)
    assert catalogue.route_calls == [("pattern1_case", "2026.08.1")]
    assert catalogue.decide_calls == []


def test_registry_404_is_controlled_error_no_correlation_id(store, catalogue: FakeCatalogue) -> None:
    registry = FakeRegistry(missing_capability=True)
    client = TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
        )
    )
    response = client.post("/v1/runs", headers=AFD, json=START_BODY)
    assert response.status_code == 422
    assert "correlation_id" not in response.json()
    assert store.all() == []


def test_draft_ref_is_controlled_error_no_correlation_id(store, catalogue: FakeCatalogue) -> None:
    registry = FakeRegistry(draft=True)
    client = TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
        )
    )
    response = client.post("/v1/runs", headers=AFD, json=START_BODY)
    assert response.status_code == 422
    assert store.all() == []


def test_get_status_returns_slim_completed_canned_message(client: TestClient) -> None:
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    correlation_id = started.json()["correlation_id"]
    response = client.get(f"/v1/runs/{correlation_id}", headers=AFD)
    assert response.status_code == 200
    assert response.json() == {
        "correlation_id": correlation_id,
        "status": "completed",
        "result": {"message": CANNED},
    }


def test_async_start_returns_202_while_graph_still_running(
    store, catalogue: FakeCatalogue, registry: FakeRegistry
) -> None:
    """Production schedule: 202 after pin; status stays running until the graph finishes."""
    import threading
    import time

    from app.core.agent_core import run_in_background

    release = threading.Event()
    entered = threading.Event()

    class SlowGraph:
        def invoke(self, state: dict) -> dict:
            entered.set()
            assert release.wait(timeout=5)
            return {"result": "async-done"}

    client = TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
            graph=SlowGraph(),
            schedule_run=run_in_background,
        )
    )
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    assert started.status_code == 202
    correlation_id = started.json()["correlation_id"]
    assert entered.wait(timeout=5)
    mid = client.get(f"/v1/runs/{correlation_id}", headers=AFD)
    assert mid.json()["status"] == "running"
    release.set()
    deadline = time.time() + 5
    while time.time() < deadline:
        body = client.get(f"/v1/runs/{correlation_id}", headers=AFD).json()
        if body.get("status") == "completed":
            assert body["result"]["message"] == "async-done"
            return
        time.sleep(0.02)
    raise AssertionError("run did not complete")


def test_unknown_correlation_id_is_404(client: TestClient) -> None:
    response = client.get("/v1/runs/corr-missing", headers=AFD)
    assert response.status_code == 404


def test_open_run_by_session_id(client: TestClient) -> None:
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    correlation_id = started.json()["correlation_id"]
    response = client.get("/v1/runs", params={"session_id": "sess-88"}, headers=AFD)
    assert response.status_code == 200
    body = response.json()
    assert body["correlation_id"] == correlation_id
    assert body["session_id"] == "sess-88"
    assert body["route_id"] == "pattern1_case"
    assert body["route_version"] == "2026.08.1"


def test_open_run_empty_when_unknown_session(client: TestClient) -> None:
    response = client.get("/v1/runs", params={"session_id": "sess-none"}, headers=AFD)
    assert response.status_code == 200
    assert response.json() == {"runs": []}


def test_completion_comes_from_graph_not_handler(store, catalogue: FakeCatalogue, registry: FakeRegistry) -> None:
    class RecordingGraph:
        def __init__(self) -> None:
            self.invoked = 0

        def invoke(self, state: dict) -> dict:
            self.invoked += 1
            return {"result": "graph-wrote-this"}

    graph = RecordingGraph()
    client = TestClient(
        create_app(store=store, catalogue=catalogue, registry=registry, graph=graph)
    )
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    correlation_id = started.json()["correlation_id"]
    assert graph.invoked == 1
    status = client.get(f"/v1/runs/{correlation_id}", headers=AFD)
    assert status.json()["result"]["message"] == "graph-wrote-this"


def test_llm_only_route_starts_without_registry(
    store, catalogue: FakeCatalogue, registry: FakeRegistry
) -> None:
    catalogue.row = {
        "route_id": "llm_pipeline",
        "route_version": "2026.08.1",
        "tool_manifest": None,
        "tool_manifest_version": None,
        "workflow_id": "llm_pipeline",
        "prompt_id": "llm_pipeline",
    }
    catalogue.workflow = {
        "stages": [
            {"id": "extract", "llm_role": "classify"},
            {"id": "rewrite", "llm_role": "synthesis"},
        ]
    }
    catalogue.prompt = {
        "host": "Do only the current stage.",
        "by_llm_role": {
            "classify": {"text": "Extract fields."},
            "synthesis": {"text": "Rewrite."},
        },
    }

    class RecordingGraph:
        def invoke(self, state: dict) -> dict:
            return {"result": "pipeline-done"}

    client = TestClient(
        create_app(store=store, catalogue=catalogue, registry=registry, graph=RecordingGraph())
    )
    body = {
        **START_BODY,
        "route_id": "llm_pipeline",
        "contract": {"tool_manifest": None, "manifest_version": None},
    }
    started = client.post("/v1/runs", headers=AFD, json=body)
    assert started.status_code == 202
    assert registry.manifest_calls == []
    pin = store.get(started.json()["correlation_id"])
    assert pin is not None
    assert [tool["id"] for tool in pin.hydrated_tools] == ["extract", "rewrite"]


def test_dynamic_graph_posts_goal_to_hydrated_tool(store, catalogue: FakeCatalogue, registry: FakeRegistry) -> None:
    calls: list[tuple[dict, dict]] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append((invoke, payload))
            return {"text": CANNED}

    client = TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
            tool_invoker=Invoker(),
            llm=FakeLlm(),
        )
    )
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    correlation_id = started.json()["correlation_id"]
    assert calls == [
        (
            {"method": "POST", "url": "http://agent-mocks:3010/tools/fetch"},
            {"record_id": "REC-77819"},
        )
    ]
    status = client.get(f"/v1/runs/{correlation_id}", headers=AFD)
    assert status.json() == {
        "correlation_id": correlation_id,
        "status": "completed",
        "result": {"message": CANNED},
    }


def test_working_session_saves_notes_on_the_run_pin(
    store, catalogue: FakeCatalogue, registry: FakeRegistry
) -> None:
    catalogue.row = {
        **catalogue.row,
        "memory_profile": {"working": "session", "loop": "none"},
    }
    client = TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
            tool_invoker=FakeInvoker(),
            llm=FakeLlm(),
        )
    )
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    pin = store.get(started.json()["correlation_id"])
    assert pin is not None
    assert pin.working == {
        "notes": [
            "Record REC-77819: widget $89.",
            CANNED,
        ],
        "slots": {
            "fetch_record": {
                "text": "Record REC-77819: widget $89.",
                "record_id": "REC-77819",
            }
        },
    }
    assert pin.checkpoint is None


def test_loop_checkpoint_saves_step_on_the_run_pin(
    store, catalogue: FakeCatalogue, registry: FakeRegistry
) -> None:
    catalogue.row = {
        **catalogue.row,
        "memory_profile": {"working": "none", "loop": "checkpoint"},
    }
    client = TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
            tool_invoker=FakeInvoker(),
            llm=FakeLlm(),
        )
    )
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    pin = store.get(started.json()["correlation_id"])
    assert pin is not None
    assert pin.working is None
    assert pin.checkpoint == {
        "step": 1,
        "stage_id": "respond",
        "result": CANNED,
        "goal": START_BODY["goal"],
        "resume_index": 2,
    }


def test_no_memory_profile_does_not_write_working_or_checkpoint(
    store, catalogue: FakeCatalogue, registry: FakeRegistry
) -> None:
    client = TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
            tool_invoker=FakeInvoker(),
            llm=FakeLlm(),
        )
    )
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    pin = store.get(started.json()["correlation_id"])
    assert pin is not None
    assert pin.working is None
    assert pin.checkpoint is None


def test_resume_reloads_working_notes(
    store, catalogue: FakeCatalogue, registry: FakeRegistry
) -> None:
    catalogue.row = {
        **catalogue.row,
        "memory_profile": {"working": "session", "loop": "none"},
    }

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            return {"text": CANNED}

    class Llm(FakeLlm):
        def complete(self, system: str, user: str) -> str:
            self.turns += 1
            if self.turns in (1, 3):
                return 'CALL fetch_record\n{"record_id": "REC-77819"}'
            return f"DONE {CANNED}"

    client = TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
            tool_invoker=Invoker(),
            llm=Llm(),
        )
    )
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    correlation_id = started.json()["correlation_id"]
    client.post(f"/v1/runs/{correlation_id}/turns", headers=AFD, json={"message": "yes"})
    pin = store.get(correlation_id)
    assert pin is not None
    assert pin.working == {
        "notes": [
            CANNED,
            "fetch_record: already completed; use prior stage outputs and choose the next tool or done.",
            CANNED,
        ],
        "slots": {"fetch_record": {"text": CANNED}},
    }


def test_resume_turn_does_not_start_a_second_run(client: TestClient, store, catalogue: FakeCatalogue) -> None:
    started = client.post("/v1/runs", headers=AFD, json=START_BODY)
    correlation_id = started.json()["correlation_id"]
    response = client.post(
        f"/v1/runs/{correlation_id}/turns",
        headers=AFD,
        json={"message": "yes"},
    )
    assert response.status_code == 200
    assert response.json()["correlation_id"] == correlation_id
    assert response.json()["status"] == "completed"
    assert len(store.all()) == 1
    assert catalogue.route_calls == [("pattern1_case", "2026.08.1"), ("pattern1_case", "2026.08.1")]


def test_resume_unknown_run_is_404(client: TestClient) -> None:
    response = client.post("/v1/runs/corr-missing/turns", headers=AFD, json={"message": "yes"})
    assert response.status_code == 404


def _purchase_refund_tools() -> list[dict]:
    return [
        {
            "id": "ocr_extract",
            "workflow_stage_id": "ocr",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/ocr"},
        },
        {
            "id": "refund_eligibility",
            "workflow_stage_id": "eligibility",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/refund/eligibility"},
        },
        {
            "id": "manual_review",
            "workflow_stage_id": "manual_review",
            "stage_type": "human_gate",
            "llm_role": "none",
            "invoke": {},
        },
        {
            "id": "post_refund",
            "workflow_stage_id": "post_refund",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/refund/post"},
        },
        {
            "id": "refund_confirm",
            "workflow_stage_id": "respond",
            "llm_role": "synthesis",
            "llm_prompt": "Confirm refund",
            "invoke": {},
        },
    ]


def test_human_gate_run_pauses_then_resumes_with_approve(monkeypatch, store) -> None:
    recorded_errors: list[object] = []
    monkeypatch.setattr(
        "app.core.execution.telemetry.record_error",
        lambda *a, **k: recorded_errors.append(a),
    )
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(str(invoke.get("url") or ""))
            return {"text": "stage ok"}

    class Llm:
        def complete(self, system: str, user: str, schema=None) -> str:
            return "Refund confirmed."

    tools = _purchase_refund_tools()
    profile = {"working": "session", "loop": "checkpoint"}
    pin = RunPin(
        correlation_id="corr-gate-approve",
        idempotency_key="job-gate-approve",
        session_id="job:refund-gate",
        route_id="purchase_refund",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=tools,
        status="running",
    )
    store.insert(pin)
    paused = run_loop(
        build_tool_graph(tools, Invoker(), llm=Llm()),
        store,
        pin,
        goal={"doc_id": "doc-1"},
        profile=profile,
    )
    assert paused.status == "waiting"
    assert recorded_errors == []
    assert calls == [
        "http://agent-mocks:3010/ocr",
        "http://agent-mocks:3010/refund/eligibility",
    ]

    service = RunService(
        store,
        FakeCatalogue(
            {
                "route_id": "purchase_refund",
                "route_version": "2026.08.1",
                "memory_profile": {"working": "session", "loop": "checkpoint"},
            }
        ),
        FakeRegistry(),
        invoker=Invoker(),
        llm=Llm(),
    )
    service._graph = None  # noqa: SLF001

    def graph_for(hydrated_tools, **kwargs):  # type: ignore[no-untyped-def]
        return build_tool_graph(
            tools,
            Invoker(),
            llm=Llm(),
            start_index=kwargs.get("start_index", 0),
        )

    service._graph_for = graph_for  # type: ignore[method-assign]
    body = service.resume(
        "corr-gate-approve",
        {"decision": "approve", "reviewer_id": "ops-1"},
    )
    assert body is not None
    assert body["status"] == "completed"
    assert calls == [
        "http://agent-mocks:3010/ocr",
        "http://agent-mocks:3010/refund/eligibility",
        "http://agent-mocks:3010/refund/post",
    ]
    updated = store.get("corr-gate-approve")
    assert updated is not None
    assert updated.working["slots"]["manual_review"]["decision"] == "approve"


def test_human_gate_resume_without_packet_stays_waiting(store, catalogue: FakeCatalogue) -> None:
    tools = _purchase_refund_tools()
    pin = RunPin(
        correlation_id="corr-gate-no-packet",
        idempotency_key="job-gate-no-packet",
        session_id="job:refund-no-packet",
        route_id="purchase_refund",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=tools,
        status="waiting",
        checkpoint={
            "stage_id": "manual_review",
            "resume_index": 3,
            "goal": {"doc_id": "doc-2"},
        },
        working={"notes": ["prior"], "slots": {}},
    )
    store.insert(pin)
    client = TestClient(create_app(store=store, catalogue=catalogue, registry=FakeRegistry()))
    bad = client.post(
        "/v1/runs/corr-gate-no-packet/turns",
        headers=AFD,
        json={"message": "not a gate packet"},
    )
    assert bad.status_code == 400
    assert store.get("corr-gate-no-packet").status == "waiting"


def _linear_checkpoint_tools() -> list[dict]:
    return [
        {
            "id": "stage_a",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/a"},
        },
        {
            "id": "stage_b",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/b"},
        },
        {
            "id": "stage_c",
            "llm_role": "none",
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/c"},
        },
    ]


def test_checkpoint_failure_then_resume_skips_completed_stages(store) -> None:
    calls: list[str] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            calls.append(str(invoke.get("url") or ""))
            return {"text": f"ok-{len(calls)}"}

    tools = _linear_checkpoint_tools()
    profile = {"working": "session", "loop": "checkpoint"}
    goal = {"job_id": "job-1"}
    pin = RunPin(
        correlation_id="corr-checkpoint-resume",
        idempotency_key="job-checkpoint-resume",
        session_id="job:checkpoint",
        route_id="generic_job",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=tools,
        status="running",
    )
    store.insert(pin)

    def on_stage(step: int, stage_id: str, state: dict) -> None:
        persist_stage(store, pin.correlation_id, profile, step, stage_id, state, tools=tools)
        if step == 0:
            raise RuntimeError("crash after stage 0")

    failed = run_loop(
        build_tool_graph(tools, Invoker(), on_stage=on_stage),
        store,
        pin,
        goal=goal,
        profile=profile,
    )
    assert failed.status == "failed"
    assert calls == ["http://agent-mocks:3010/a"]
    assert failed.checkpoint is not None
    assert failed.checkpoint["step"] == 0
    assert failed.checkpoint["resume_index"] == 1
    assert failed.checkpoint["goal"] == goal

    service = RunService(
        store,
        FakeCatalogue(
            {
                "route_id": "generic_job",
                "route_version": "2026.08.1",
                "autonomy_mode": 2,
                "memory_profile": profile,
            }
        ),
        FakeRegistry(),
        invoker=Invoker(),
    )
    service._graph = None  # noqa: SLF001

    def on_stage_resume(step: int, stage_id: str, state: dict) -> None:
        persist_stage(store, pin.correlation_id, profile, step, stage_id, state, tools=tools)

    def graph_for(hydrated_tools, **kwargs):  # type: ignore[no-untyped-def]
        return build_tool_graph(
            tools,
            Invoker(),
            on_stage=on_stage_resume,
            start_index=kwargs.get("start_index", 0),
        )

    service._graph_for = graph_for  # type: ignore[method-assign]
    body = service.resume("corr-checkpoint-resume", {"resume": True})
    assert body is not None
    assert body["status"] == "completed"
    assert calls == [
        "http://agent-mocks:3010/a",
        "http://agent-mocks:3010/b",
        "http://agent-mocks:3010/c",
    ]


def test_loop_none_failure_is_not_recoverable(store) -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            raise RuntimeError("boom")

    tools = _linear_checkpoint_tools()[:1]
    pin = RunPin(
        correlation_id="corr-no-checkpoint",
        idempotency_key="job-no-checkpoint",
        session_id="job:no-checkpoint",
        route_id="generic_job",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=tools,
        status="running",
    )
    store.insert(pin)
    try:
        run_loop(
            build_tool_graph(tools, Invoker()),
            store,
            pin,
            goal={"job_id": "job-2"},
            profile={"working": "none", "loop": "none"},
        )
    except RuntimeError:
        pass
    updated = store.get("corr-no-checkpoint")
    assert updated is not None
    assert updated.status == "failed"
    assert updated.checkpoint is None

    client = TestClient(
        create_app(
            store=store,
            catalogue=FakeCatalogue(
                {
                    "route_id": "generic_job",
                    "route_version": "2026.08.1",
                    "memory_profile": {"loop": "none"},
                }
            ),
            registry=FakeRegistry(),
            tool_invoker=Invoker(),
        )
    )
    response = client.post("/v1/runs/corr-no-checkpoint/turns", headers=AFD, json={"resume": True})
    assert response.status_code == 400


def test_customer_ask_pauses_then_resumes_with_message(store) -> None:
    payloads: list[dict] = []

    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            payloads.append(payload)
            return {"text": "Record REC-77819: widget $149."}

    class Llm(TextLlm):
        def __init__(self) -> None:
            self.turns = 0

        def complete(self, system: str, user: str, schema=None) -> str:
            self.turns += 1
            if "Record REC-77819" in user:
                return "DONE Record REC-77819: widget $149."
            if "customer: REC-77819" in user:
                return 'CALL fetch_record\n{"record_id":"REC-77819"}'
            return "ASK Please provide a record id."

    tools = [
        {
            "id": "fetch_record",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {"record_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/fetch"},
        }
    ]
    row = {
        "route_id": "pattern1_case",
        "route_version": "2026.08.1",
        "autonomy_mode": 1,
        "max_loop_steps": 6,
        "prompt_id": "pattern1_case",
        "memory_profile": {"working": "session", "loop": "checkpoint"},
    }
    pin = RunPin(
        correlation_id="corr-ask-1",
        idempotency_key="chat-ask-1",
        session_id="chat-ask-1",
        route_id="pattern1_case",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=tools,
        status="running",
    )
    store.insert(pin)
    paused = run_loop(
        build_agent_loop(tools, Invoker(), Llm(), max_steps=6),
        store,
        pin,
        goal={"utterance": "need help"},
        profile=row["memory_profile"],
    )
    assert paused.status == "waiting"
    assert paused.checkpoint["waiting_for"] == "customer_ask"
    assert paused.result["message"].startswith("Please provide")

    catalogue = FakeCatalogue(row)
    catalogue.prompt = {"host": "Pattern 1 coordinator."}
    service = RunService(
        store,
        catalogue,
        FakeRegistry(),
        invoker=Invoker(),
        llm=Llm(),
    )
    body = service.resume("corr-ask-1", {"message": "REC-77819"})
    assert body is not None
    assert body["status"] == "completed"
    assert payloads == [{"record_id": "REC-77819"}]


def test_customer_ask_resume_is_idempotent_when_reply_already_recorded(store) -> None:
    class Invoker:
        def call(self, invoke: dict, payload: dict) -> dict:
            return {"text": "Record REC-77819: widget $149."}

    class Llm(TextLlm):
        def complete(self, system: str, user: str, schema=None) -> str:
            if "Record REC-77819" in user:
                return "DONE Record REC-77819: widget $149."
            if "customer: REC-77819" in user:
                return 'CALL fetch_record\n{"record_id":"REC-77819"}'
            return "ASK Please provide a record id."

    tools = [
        {
            "id": "fetch_record",
            "input_schema": {
                "type": "object",
                "required": ["record_id"],
                "properties": {"record_id": {"type": "string"}},
            },
            "invoke": {"method": "POST", "url": "http://agent-mocks:3010/tools/fetch"},
        }
    ]
    row = {
        "route_id": "pattern1_case",
        "route_version": "2026.08.1",
        "autonomy_mode": 1,
        "max_loop_steps": 6,
        "prompt_id": "pattern1_case",
        "memory_profile": {"working": "session", "loop": "checkpoint"},
    }
    pin = RunPin(
        correlation_id="corr-ask-dup",
        idempotency_key="chat-ask-dup",
        session_id="chat-ask-dup",
        route_id="pattern1_case",
        route_version="2026.08.1",
        activation_target=None,
        agent_client_id=None,
        hydrated_tools=tools,
        status="waiting",
        checkpoint={
            "waiting_for": "customer_ask",
            "stage_id": "customer_ask",
            "resume_loop_step": 1,
            "goal": {"utterance": "need help"},
        },
        working={
            "notes": ["ask: Please provide a record id.", "customer: REC-77819"],
            "slots": {},
        },
        result={"message": "Please provide a record id."},
    )
    store.insert(pin)
    catalogue = FakeCatalogue(row)
    catalogue.prompt = {"host": "Pattern 1 coordinator."}
    service = RunService(
        store,
        catalogue,
        FakeRegistry(),
        invoker=Invoker(),
        llm=Llm(),
    )
    body = service.resume("corr-ask-dup", {"message": "REC-77819"})
    assert body is not None
    assert body["status"] == "completed"
    finished = store.get("corr-ask-dup")
    assert finished is not None
    notes = finished.working["notes"] if finished.working else []
    assert notes.count("customer: REC-77819") == 1
