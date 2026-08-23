import json

from fastapi.testclient import TestClient

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
    assert body["correlation_id"]
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
    assert pin.hydrated_tools[0]["id"] == "account_fee_lookup"
    assert pin.hydrated_tools[0]["invoke"]["url"] == "http://tool-mock:3010/fees/explain"


def test_catalogue_get_uses_pinned_version_never_active(
    client: TestClient, catalogue: FakeCatalogue
) -> None:
    client.post("/v1/runs", headers=AFD, json=START_BODY)
    assert catalogue.route_calls == [("fee_explain", "2026.08.1")]
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
    assert body["route_id"] == "fee_explain"
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
            {"method": "POST", "url": "http://tool-mock:3010/fees/explain"},
            {"utterance": "Why was I charged $42?"},
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
    assert pin.working == {"notes": [CANNED, CANNED]}
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
        "goal": {"utterance": "Why was I charged $42?"},
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
    client.post(f"/v1/runs/{correlation_id}/turns", headers=AFD, json={"message": "yes"})
    pin = store.get(correlation_id)
    assert pin is not None
    assert pin.working == {"notes": [CANNED, CANNED, CANNED]}


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
    assert catalogue.route_calls == [("fee_explain", "2026.08.1"), ("fee_explain", "2026.08.1")]


def test_resume_unknown_run_is_404(client: TestClient) -> None:
    response = client.post("/v1/runs/corr-missing/turns", headers=AFD, json={"message": "yes"})
    assert response.status_code == 404
