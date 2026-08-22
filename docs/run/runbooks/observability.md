# Observability runbooks (local Fabric)

Symptom-based. Causes (CPU alone) stay on dashboards.

## Decide error rate high

**Means:** Front Door → Data Plane `/v1/intent/decide` is failing or timing out.

**First query (Tempo):** `{.service.name="agent-data-plane" && .http.route="/v1/intent/decide"}`  
**First query (Prom):** HTTP server error rate for `agent-data-plane`.

**Escalation:** Check Data Plane logs for `intent.decide.*`; verify Postgres `adp` and pool metrics.

## Hydrate failure rate high

**Means:** Agent Runtime cannot pin catalogue/manifest/capability before `202`.

**First query (Loki):** `{service="agent-runtime"} | json | event="run.hydrate.failed"`  
**First query (Tempo):** `{.service.name="agent-runtime"}` spans named `hydrate`.

**Escalation:** Confirm route pin versions exist as `published` in ADP/ACR; check Registry 404s.

## Journey completion drop (`fee_explain`)

**Means:** `run.accepted` rises but `run.completed` / `chat.events.delivered` does not.

**First query (Prom):** `fabric_journey_outcome_total{journey_id="chat.fee_explain"}` or `job.fee_explain` by `outcome`.  
**First query (Tempo):** `{.correlation_id="<id>"}` across AFD → AR (`graph.invoke`, `tool.invoke`, `llm.complete`).

**Escalation:** Inspect AR `graph.invoke` span and AR logs; check Runtime DB `ar`.
