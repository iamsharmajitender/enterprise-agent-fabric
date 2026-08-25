# Agent Front Door

Channel ingress for the local fabric. One Java process on port **3005**. Jobs `/v1/jobs*` is live. Chat `/v1/assistant/*` is the same process and port; those routes land after the jobs path.

Docs map: [docs/README.md](../docs/README.md). Frozen examples: [docs/05-reference/](../docs/05-reference/README.md).

## Job

Accept a named `route_id` from a partner/system caller, entitle (Layer ① only — no keyword classify, no `clarify`), freeze, start Agent Runtime, return `202 { "correlation_id" }`. Callers may see `route_id` / `correlation_id` (FR-5 is chat-only). Poll status from Runtime HTTP. Do **not** add a second fleet, hostname, or Compose service.

## Port / stack

| | |
| --- | --- |
| Port | **3005** |
| Stack | Java 21, Spring Boot 3.5, Flyway |
| Database | `afd` (schema `frontdoor`; jobs freeze is in-memory until the chat-path table) |
| Compose | `agent-front-door` — the only Front Door service |

## Hexagonal layout

| Package | Role |
| --- | --- |
| `domain` | Records and exceptions. No Spring or SQL. |
| `application` | `JobsService`, ports (`DecidePort`, `CataloguePort`, `RuntimePort`, `FreezeStore`) |
| `adapters.in.http` | `JobsController`, `ChannelAuthFilter`, `HealthController` |
| `adapters.out.http` | Data Plane and Runtime clients (`X-Workload: afd`) |

## Auth

Channel (humans / jobs callers → this box):

```http
Authorization: Bearer stub
X-Stub-Claims: {"sub":"jane","emts":{"accounts:read":true}}
```

Missing or invalid bearer: **401**. Stub user `jane` has `accounts:read`, which `fee_explain` requires. Details: [`05-reference/stub-auth.md`](../docs/05-reference/stub-auth.md).

Outbound to Data Plane and Runtime: `Authorization: Bearer fabric-internal` and `X-Workload: afd`. The JDK HTTP client is pinned to **HTTP/1.1** (Runtime is uvicorn; h2c upgrade fails closed).

## APIs

| Method | Path | Who | Response |
| --- | --- | --- | --- |
| `GET` | `/health` | Anyone | `{"status":"UP"}` |
| `POST` | `/v1/jobs` | Channel bearer | `202 {"correlation_id"}`. Layer ①: `ingress: "jobs"` + explicit `route_id`. No Layer ②. Never returns chat `clarify`. Missing claims / unknown route → **403**, do not start Runtime. Duplicate `idempotency_key` returns the original id (Runtime enforces; this process retries the same start). |
| `GET` | `/v1/jobs/{correlation_id}` | Channel bearer | Slim Runtime status / result. **No** Data Plane call. |

Chat `/v1/assistant/hints`, `turns`, and `events` are not served yet (same process later).

### Jobs start

Request ([`05-reference/jobs-start.json`](../docs/05-reference/jobs-start.json)):

```json
{
  "route_id": "fee_explain",
  "idempotency_key": "job-fee-explain:v1",
  "payload": { "account_id": "acc-42" }
}
```

Response ([`05-reference/jobs-accepted.json`](../docs/05-reference/jobs-accepted.json)): `202 {"correlation_id":"…"}`.

Decide body this box sends ([`05-reference/decide-jobs-route.json`](../docs/05-reference/decide-jobs-route.json)): `ingress: "jobs"`, `route_id` set, `message` null.

If Runtime does not return `202`, this box responds **503** and does not invent a `correlation_id`. Retry with the same idempotency key.

## Business events

Front Door emits **only** these, from `BusinessEvents.emit`. Not Kafka. No utterance, tokens, or claims. Decide outcomes are Data Plane; hydrate/complete are Runtime.

### Chat (`AssistantService`)

| Event | When |
| --- | --- |
| `chat.turn.received` | Jane posts a turn (before decide) |
| `chat.run.accepted` | Freeze + Runtime start succeeded |
| `chat.events.delivered` | Poll/SSE sees run completed |

### Jobs (`JobsService`)

| Event | When |
| --- | --- |
| `job.entitle.accepted` | Job POST accepted for entitle |
| `job.entitle.rejected` | Decide did not return `route` |
| `job.run.accepted` | Runtime start succeeded |

Full journey list: [root README — Business events](../README.md#business-events).

## Contracts

- [`05-reference/jobs-start.json`](../docs/05-reference/jobs-start.json)
- [`05-reference/jobs-accepted.json`](../docs/05-reference/jobs-accepted.json)
- [`05-reference/decide-jobs-route.json`](../docs/05-reference/decide-jobs-route.json)
- [`05-reference/stub-auth.md`](../docs/05-reference/stub-auth.md)

## Tables / schema

Flyway on `afd` creates schema `frontdoor` (`V1__frontdoor.sql`). Jobs freeze is **`InMemoryFreezeStore`**, keyed by `session_id` = `job:{idempotency_key}`. It is not the catalogue and not the Runtime run pin. A durable freeze table lands with the chat path.

## Sibling calls

| Direction | Call | Notes |
| --- | --- | --- |
| Out | Data Plane `POST /v1/intent/decide` | AFD-only. Jobs: Layer ① entitle + bind. No keyword classify. |
| Out | Data Plane `GET /v1/catalog/routes/{id}?route_version=` | Pinned row after `outcome=route`. |
| Out | Runtime `POST /v1/runs` | `mode: new`. AFD workload. |
| Out | Runtime `GET /v1/runs/{correlation_id}` | Jobs poll. No Data Plane on this path. |

## Non-goals

- A second Front Door fleet, hostname, or Compose service
- Kafka `{runs_topic}` / SSE
- Chat `/v1/assistant/*` (same process, later)
- Calling decide from Runtime or Control Plane
- Inventing `correlation_id` on Runtime failure

## Tests

Image build runs `mvn test`. Locally (JDK 21):

```bash
mvn -q -B test
```

Covers jobs start, entitle miss (403, no Runtime start), duplicate idempotency key, GET status, unknown id 404.

Live proof (compose up):

```bash
./docs/run/dummy-request/run-job.sh --list
./docs/run/dummy-request/run-job.sh fee_explain
./docs/run/dummy-request/run-chat.sh --list
./docs/run/dummy-request/run-chat.sh fee_explain
```

Jobs mint a new `idempotency_key` and payload ids (`account_id`, `claim_id`, …). `correlation_id` comes back from Front Door. Same key twice still returns the original id (`./docs/run/dummy-request/run-job.sh --check-idempotency fee_explain`). `claims_adjudicate` needs claim `claims:read`. Chats mint a new `session_id`; `fee_explain` needs `accounts:read`.
