# Agent Front Door

Channel ingress for the local fabric. One Java process on port **3005**. Jobs `/v1/jobs*` and chat `/v1/assistant/*` share this process and port — not a second fleet.

Docs map: [docs/README.md](../agent-fabric-docs/README.md). Frozen examples: [docs/05-reference/](../agent-fabric-docs/05-reference/README.md).

## Job

Accept channel traffic, entitle/classify via Data Plane, freeze the pin, start Agent Runtime, return `202 { "correlation_id" }` (jobs) or a FR-5-slim assistant body (chat). Poll Runtime over HTTP. Do **not** invent `correlation_id` when Runtime fails; do **not** add a second Compose service.

## Port / stack

| | |
| --- | --- |
| Port | **3005** |
| Stack | Java 21, Spring Boot 3.5, Flyway |
| Database | `afd` (schema `frontdoor`) |
| Compose | `agent-front-door` — the only Front Door service |

## Hexagonal layout

| Package | Role |
| --- | --- |
| `domain` | Records and exceptions. No Spring or SQL. |
| `application` | `JobsService`, `AssistantService`, ports (`DecidePort`, `CataloguePort`, `RuntimePort`, `FreezeStore`) |
| `adapters.in.http` | `JobsController`, `AssistantController`, `ChannelAuthFilter`, `HealthController` |
| `adapters.out.http` | Data Plane and Runtime clients (`X-Workload: afd`) |
| `adapters.out.jdbc` | `JdbcFreezeStore` |

## Auth

Channel (humans / jobs callers → this box):

```http
Authorization: Bearer stub
X-Stub-Claims: {"sub":"jane","emts":{"accounts:read":true}}
```

Missing or invalid bearer: **401**. Stub user `jane` has `accounts:read`, which `fee_explain` requires. Details: [`05-reference/stub-auth.md`](../agent-fabric-docs/05-reference/stub-auth.md).

Outbound to Data Plane and Runtime: `Authorization: Bearer fabric-internal` and `X-Workload: afd`. The JDK HTTP client is pinned to **HTTP/1.1** (Runtime is uvicorn; h2c upgrade fails closed).

## APIs

| Method | Path | Who | Response |
| --- | --- | --- | --- |
| `GET` | `/health` | Anyone | `{"status":"UP"}` |
| `POST` | `/v1/jobs` | Channel bearer | `202 {"correlation_id"}`. Layer ① only (`ingress: "jobs"` + explicit `route_id`). Never chat `clarify`. Missing claims / unknown route → **403**, do not start Runtime. Duplicate `idempotency_key` returns the original id. |
| `GET` | `/v1/jobs/{correlation_id}` | Channel bearer | Slim Runtime status / result. **No** Data Plane call. |
| `GET` | `/v1/assistant/hints` | Channel bearer | Eligible chip hints for the stub claims |
| `POST` | `/v1/assistant/turns` | Channel bearer | First turn: decide → freeze → start AR. Live freeze: **skip decide**, resume / continue. FR-5 slim JSON. |
| `GET` | `/v1/assistant/sessions/{sessionId}/events` | Channel bearer | Poll assistant events / run progress |

### FR-5 (chat JSON)

Assistant responses must **not** contain: `route_id`, `run_id`, `agent_client_id`, `confidence`, `router_layer`. Jobs callers may see `route_id` / `correlation_id`.

### Jobs start

Request ([`05-reference/jobs-start.json`](../agent-fabric-docs/05-reference/jobs-start.json)):

```json
{
  "route_id": "fee_explain",
  "idempotency_key": "job-fee-explain:v1",
  "payload": { "account_id": "acc-42" }
}
```

Response ([`05-reference/jobs-accepted.json`](../agent-fabric-docs/05-reference/jobs-accepted.json)): `202 {"correlation_id":"…"}`.

Decide body this box sends ([`05-reference/decide-jobs-route.json`](../agent-fabric-docs/05-reference/decide-jobs-route.json)): `ingress: "jobs"`, `route_id` set, `message` null.

If Runtime does not return `202`, this box responds **503** and does not invent a `correlation_id`. Retry with the same idempotency key.

### Chat continuation

A live freeze (`session_id` → `correlation_id` + route pin) **skips decide** on the next turn. Freeze miss → AR open-run by `session_id` over HTTP (this box never reads `ar` SQL).

## Business events

Front Door emits **only** these, from `BusinessEvents.emit`. Not Kafka. No utterance, tokens, or claims. Decide outcomes are Data Plane; hydrate/complete are Runtime.

### Chat (`AssistantService`)

| Event | When |
| --- | --- |
| `chat.turn.received` | User posts a turn (before decide) |
| `chat.run.started` | Freeze + Runtime start succeeded |
| `chat.run.delivered` | Poll sees run completed |

### Jobs (`JobsService`)

| Event | When |
| --- | --- |
| `job.entitlement.accepted` | Job POST accepted for entitle |
| `job.entitlement.rejected` | Decide did not return `route` |
| `job.run.started` | Runtime start succeeded |
| `job.run.delivered` | Status poll sees run completed |

Full journey list: [root README — Business events](../README.md#business-events).

## Contracts

- [`05-reference/jobs-start.json`](../agent-fabric-docs/05-reference/jobs-start.json)
- [`05-reference/jobs-accepted.json`](../agent-fabric-docs/05-reference/jobs-accepted.json)
- [`05-reference/decide-jobs-route.json`](../agent-fabric-docs/05-reference/decide-jobs-route.json)
- [`05-reference/assistant-turn-request.json`](../agent-fabric-docs/05-reference/assistant-turn-request.json)
- [`05-reference/assistant-turn-accepted.json`](../agent-fabric-docs/05-reference/assistant-turn-accepted.json)
- [`05-reference/stub-auth.md`](../agent-fabric-docs/05-reference/stub-auth.md)

## Tables / schema

Flyway `V1__frontdoor.sql` on `afd`:

| Table | Role |
| --- | --- |
| `frontdoor.freeze` | Stickiness pin: `session_id` PK, `idempotency_key`, `route_id`, `route_version`, `activation_target`, `agent_client_id`, `correlation_id`, `expires_at` (TTL **45 min** via `JdbcFreezeStore`) |
| `frontdoor.opaque_ids` | Opaque hint ids per session |

Jobs use `session_id = job-{uuid}` (or `sub-{uuid}` when the idempotency key is a subagent start). Chat mints `chat-{uuid}`. Freeze is **not** the catalogue and **not** the Runtime run pin. Pin miss uses Runtime `GET /v1/runs?session_id=` — never AR SQL from this box.

## Sibling calls

| Direction | Call | Notes |
| --- | --- | --- |
| Out | Data Plane `POST /v1/intent/decide` | AFD-only. Jobs: Layer ①. Chat first turn: ① then ②. |
| Out | Data Plane `GET /v1/intent/eligible` | Hints |
| Out | Data Plane `GET /v1/catalog/routes/{id}?route_version=` | Pinned row after `outcome=route` |
| Out | Runtime `POST /v1/runs` | `mode: new`. AFD workload. |
| Out | Runtime `GET /v1/runs/{correlation_id}` | Jobs / events poll |
| Out | Runtime `GET /v1/runs?session_id=` | Open-run on freeze miss |
| Out | Runtime `POST /v1/runs/{id}/turns` | Chat continuation / human_gate / checkpoint resume |

## Non-goals

- A second Front Door fleet, hostname, or Compose service
- Kafka `{runs_topic}` as the delivery bus (local poll instead)
- Calling decide from Runtime or Control Plane
- Inventing `correlation_id` on Runtime failure
- Reading `ar` Postgres from this process

## Tests

Image build runs `mvn test`. Locally (JDK 21):

```bash
mvn -q -B test
```

Covers jobs start, entitle miss (403, no Runtime start), duplicate idempotency key, GET status, FR-5 forbidden keys on assistant JSON, chat turn / continuation.

Live proof (compose up):

```bash
./agent-fabric-scripts/catalogue-seed/run-chat.sh shopassist_case_ask
```

Chats mint a new `session_id`. `shopassist_case_ask` needs claim `support:case`.
