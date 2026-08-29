from app.agents.jobs_client import resolve_jobs_url


def test_resolve_jobs_url_maps_catalogue_host(monkeypatch) -> None:
    monkeypatch.setenv("AFD_URL", "http://agent-front-door:3005")
    assert (
        resolve_jobs_url("https://api-afd.internal/v1/jobs")
        == "http://agent-front-door:3005/v1/jobs"
    )
