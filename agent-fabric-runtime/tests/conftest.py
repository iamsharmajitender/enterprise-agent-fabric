from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from in_memory_store import InMemoryRunStore

AFD = {"Authorization": "Bearer fabric-internal", "X-Workload": "afd"}

START_BODY: dict[str, Any] = {
    "mode": "new",
    "idempotency_key": "sess-88:shopassist_case:v1",
    "session_id": "sess-88",
    "route_id": "shopassist_case",
    "route_version": "2026.08.1",
    "activation_target": "http://agent-runtime:3008/v1/runs",
    "agent_client_id": "agent-shopassist-case",
    "contract": {
        "tool_manifest": "shopassist_case",
        "manifest_version": "2026.08.1",
        "policy_profile": "read_only_standard",
        "model_profile": "stub",
        "max_loop_steps": 12,
    },
    "goal": {
        "message": "My blue jacket ORD-77819 arrived damaged and I was charged twice. Full refund please."
    },
}

CANNED = "Handoff opened: hof-1."

CATALOGUE_ROW = {
    "route_id": "shopassist_case",
    "route_version": "2026.08.1",
    "activation_target": "http://agent-runtime:3008/v1/runs",
    "agent_client_id": "agent-shopassist-case",
    "tool_manifest": "shopassist_case",
    "tool_manifest_version": "2026.08.1",
    "autonomy_mode": 1,
    "max_loop_steps": 12,
    "prompt_id": "shopassist_case",
}

MANIFEST = {
    "manifest_id": "shopassist_case",
    "manifest_version": "2026.08.1",
    "status": "published",
    "tools": [
        {
            "name": "lookup_order",
            "capability_id": "lookup_order",
            "capability_version": "1.0.0",
            "pdp_action": "lookup_order",
            "risk_tier": "low",
        },
        {
            "name": "escalate_to_human",
            "capability_id": "escalate_to_human",
            "capability_version": "1.0.0",
            "pdp_action": "escalate_to_human",
            "risk_tier": "high",
        },
    ],
}

CAPABILITY = {
    "id": "lookup_order",
    "version": "1.0.0",
    "kind": "domain",
    "status": "published",
    "input_schema": {
        "type": "object",
        "required": ["order_id"],
        "properties": {"order_id": {"type": "string"}},
    },
    "output_schema": {"type": "object"},
    "invoke": {"method": "POST", "url": "http://agent-mocks:3010/shopassist/lookup_order"},
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
        self.prompt: dict[str, Any] = {
            "prompt_id": "shopassist_case",
            "prompt_version": "2026.08.1",
            "host": "Pattern 1 shopassist stub",
        }
        self.corpora: dict[str, dict[str, Any]] = {}

    def get_corpus(self, corpus_id: str) -> dict[str, Any]:
        from app.agents.hydrate import HydrateError

        if corpus_id not in self.corpora:
            raise HydrateError(f"corpus miss {corpus_id}")
        return self.corpora[corpus_id]

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
        url = str(invoke.get("url") or "")
        if "lookup_order" in url:
            return {
                "text": "Order ORD-77819: blue jacket $89 delivered yesterday.",
                "order_id": "ORD-77819",
                "item_id": "ITM-JACKET",
            }
        return {"text": CANNED, "handoff_id": "hof-1"}


class FakeLlm:
    def __init__(self) -> None:
        self.turns = 0

    def complete(self, system: str, user: str) -> str:
        """Pattern 1 stub: CALL lookup_order when ORD is in goal, then DONE."""
        self.turns += 1
        if self.turns == 1:
            return 'CALL lookup_order\n{"order_id": "ORD-77819"}'
        return f"DONE {CANNED}"


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
            llm=FakeLlm(),
        )
    )
