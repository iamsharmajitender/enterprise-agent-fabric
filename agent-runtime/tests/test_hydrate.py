import pytest

from app.hydrate import HydrateError, hydrate
from tests.conftest import START_BODY, FakeCatalogue, FakeRegistry


def test_hydrate_fetches_manifest_and_each_capability() -> None:
    catalogue = FakeCatalogue()
    registry = FakeRegistry()
    tools = hydrate(START_BODY, catalogue, registry)
    assert catalogue.route_calls == [("fee_explain", "2026.08.1")]
    assert registry.manifest_calls == [("fee_explain_v1", "2026.08.1")]
    assert registry.capability_calls == [("account_fee_lookup", "1.0.0")]
    assert tools[0]["id"] == "account_fee_lookup"
    assert catalogue.decide_calls == []


def test_hydrate_fails_when_capability_missing() -> None:
    with pytest.raises(HydrateError):
        hydrate(START_BODY, FakeCatalogue(), FakeRegistry(missing_capability=True))


def test_hydrate_requires_pinned_catalogue_version() -> None:
    body = {**START_BODY, "route_version": ""}
    with pytest.raises(HydrateError):
        hydrate(body, FakeCatalogue(), FakeRegistry())


def test_hydrate_fails_on_catalogue_miss() -> None:
    with pytest.raises(HydrateError):
        hydrate(START_BODY, FakeCatalogue(missing=True), FakeRegistry())
