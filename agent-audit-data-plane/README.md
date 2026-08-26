# Agent Audit Data Plane (AADP)

Append-only fabric **evidence** store. Port **3012** (local Compose). Database: Postgres `audit`.

## Boundaries

| Does | Does not |
| --- | --- |
| `POST /v1/audit/events` ingest (idempotent on `event_id`) | Decide, pin, start Runtime |
| `GET /v1/audit/chains/{correlation_id}` | Host the ops UI (see agent-audit-control-plane) |
| `GET /v1/audit/sessions/{session_id}` | Rewrite history (no update/delete APIs) |
| `GET /v1/audit/workflows?limit&offset&status` | `status=completed` (default: terminal `completed` **and** `failed`) or `in_progress`. Rows may include `parent_correlation_id` for `kind=agent` children. |

Producers: AFD, ADP, AR, ACR (async HTTP). Control plane AACP queries only.

**Workload:** callers may send `X-Workload` (`afd`, `adp`, `ar`, `acr`, `aacp`). Local stub auth; IdP later.

**Ports note:** `3010` is agent-fabric-mocks; AADP uses **3012**, AACP **3013**.

## Contracts

Envelope + examples: [`docs/05-reference/audit-event-envelope.json`](../docs/05-reference/audit-event-envelope.json). Plan: [`docs/tasks/audit-plan.md`](../docs/tasks/audit-plan.md).

## Retention / redaction (local defaults)

- **Retention:** keep events for local demos indefinitely; production should set a TTL (e.g. 30–90 days) and archive — see task A16.
- **Redaction:** payload deny-list includes `utterance`, `message`, `claims`, `authorization`, `prompt`, `completion`. Prefer `*_hash` / `*_digest` fields.

## Run

```bash
# against local Postgres with DB audit
mvn -q -DskipTests spring-boot:run
curl -sf localhost:3012/health
```
