from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from in_memory_store import InMemoryRunStore

AFD = {"Authorization": "Bearer fabric-internal", "X-Workload": "afd"}

START_BODY: dict[str, Any] = {
    "mode": "new",
    "idempotency_key": "sess-88:fee_explain:v1",
    "session_id": "sess-88",
    "route_id": "fee_explain",
    "route_version": "2026.08.1",
    "activation_target": "http://agent-runtime:3008/v1/runs",
    "agent_client_id": "fee-explain-v1",
    "contract": {
        "tool_manifest": "fee_explain_v1",
        "manifest_version": "2026.08.1",
        "policy_profile": "accounts_read",
        "model_profile": "stub",
        "max_loop_steps": 12,
    },
    "goal": {"utterance": "Why was I charged $42?"},
}

CANNED = "Fee of $42 is the monthly account charge."

CATALOGUE_ROW = {
    "route_id": "fee_explain",
    "route_version": "2026.08.1",
    "activation_target": "http://agent-runtime:3008/v1/runs",
    "agent_client_id": "fee-explain-v1",
    "tool_manifest": "fee_explain_v1",
    "tool_manifest_version": "2026.08.1",
}

MANIFEST = {
    "manifest_id": "fee_explain_v1",
    "manifest_version": "2026.08.1",
    "status": "published",
    "tools": [
        {
            "name": "account_fee_lookup",
            "capability_id": "account_fee_lookup",
            "capability_version": "1.0.0",
            "pdp_action": "account_fee_lookup",
            "risk_tier": "low",
        }
    ],
}

CAPABILITY = {
    "id": "account_fee_lookup",
    "version": "1.0.0",
    "kind": "domain",
    "status": "published",
    "input_schema": {"type": "object"},
    "output_schema": {"type": "object"},
    "invoke": {"method": "POST", "url": "http://tool-mock:3010/fees/explain"},
}


class FakeCatalogue:
    def __init__(self, row: dict[str, Any] | None = None, *, missing: bool = False) -> None:
        self.row = CATALOGUE_ROW if row is None else row
        self.missing = missing
        self.route_calls: list[tuple[str, str]] = []
        self.decide_calls: list[Any] = []
        self.workflow_calls: list[str] = []
        self.prompt_calls: list[str] = []
        self.workflow: dict[str, Any] = {}
        self.prompt: dict[str, Any] = {}

    def get_route(self, route_id: str, route_version: str) -> dict[str, Any]:
        from app.agents.hydrate import HydrateError

        self.route_calls.append((route_id, route_version))
        if not route_version:
            raise HydrateError("pinned version required")
        if self.missing:
            raise HydrateError(f"catalogue miss {route_id}@{route_version}")
        return self.row

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        self.workflow_calls.append(workflow_id)
        return self.workflow

    def get_prompt(self, prompt_id: str) -> dict[str, Any]:
        self.prompt_calls.append(prompt_id)
        return self.prompt

    def decide(self, *_args: Any, **_kwargs: Any) -> None:
        self.decide_calls.append(True)
        raise AssertionError("AR must not call decide")


class FakeRegistry:
    def __init__(
        self,
        *,
        manifest: dict[str, Any] | None = None,
        capability: dict[str, Any] | None = None,
        missing_manifest: bool = False,
        missing_capability: bool = False,
        draft: bool = False,
    ) -> None:
        self.manifest = MANIFEST if manifest is None else manifest
        self.capability = CAPABILITY if capability is None else capability
        self.missing_manifest = missing_manifest
        self.missing_capability = missing_capability
        self.draft = draft
        self.manifest_calls: list[tuple[str, str]] = []
        self.capability_calls: list[tuple[str, str]] = []

    def get_manifest(self, manifest_id: str, manifest_version: str) -> dict[str, Any]:
        from app.agents.hydrate import HydrateError

        self.manifest_calls.append((manifest_id, manifest_version))
        if self.missing_manifest or self.draft:
            raise HydrateError(f"manifest miss {manifest_id}@{manifest_version}")
        return self.manifest

    def get_capability(self, capability_id: str, version: str) -> dict[str, Any]:
        from app.agents.hydrate import HydrateError

        self.capability_calls.append((capability_id, version))
        if self.missing_capability or self.draft:
            raise HydrateError(f"capability miss {capability_id}@{version}")
        body = dict(self.capability)
        body["id"] = capability_id
        return body


class FakeInvoker:
    def call(self, invoke: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        return {"text": CANNED}


@pytest.fixture
def store() -> InMemoryRunStore:
    return InMemoryRunStore()


@pytest.fixture
def catalogue() -> FakeCatalogue:
    return FakeCatalogue()


@pytest.fixture
def registry() -> FakeRegistry:
    return FakeRegistry()


@pytest.fixture
def invoker() -> FakeInvoker:
    return FakeInvoker()


@pytest.fixture
def client(
    store: InMemoryRunStore,
    catalogue: FakeCatalogue,
    registry: FakeRegistry,
    invoker: FakeInvoker,
) -> TestClient:
    return TestClient(
        create_app(
            store=store,
            catalogue=catalogue,
            registry=registry,
            tool_invoker=invoker,
        )
    )
