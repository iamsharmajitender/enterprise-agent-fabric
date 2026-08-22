# Enterprise Agent Fabric

Local fabric that **classifies a chat turn onto a route**, then runs that route. Five services, one Compose file, four Postgres databases. Kafka, IdP, and the LLM are stubbed.

Demo utterance: `"Why was I charged $42?"` → route `fee_explain` @ `2026.08.1` → `"Fee of $42 is the monthly account charge."`

Jobs path swimlane: [docs/run/diagrams/swimlane-jobs-fee-explain.html](docs/run/diagrams/swimlane-jobs-fee-explain.html) (`./docs/run/dummy-jobs/1-autonomous/fee_explain.sh`).

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- From the **repository root** for every command below

## Run

```bash
./docs/run/scripts/start-app.sh
```

That is `docker compose up --build -d`. Stop (volumes kept):

```bash
./docs/run/scripts/stop-app.sh
```

Reload catalogue seed (deletes, then inserts):

```bash
./docs/run/scripts/seed-db.sh
```

| Command | What it does |
| --- | --- |
| `./docs/run/scripts/start-app.sh` | Build and start in the background |
| `./docs/run/scripts/stop-app.sh` | Stop containers (volumes kept) |
| `./docs/run/scripts/seed-db.sh` | Delete and reload teaching + lifecycle seed |
| `docker compose -f docs/run/compose/docker-compose.yml ps` | Process status |
| `docker compose -f docs/run/compose/docker-compose.yml logs -f` | Follow all logs |
| `docker compose -f docs/run/compose/docker-compose.yml logs -f agent-data-plane` | One service |
| `docker compose -f docs/run/compose/docker-compose.yml logs -f otel-lgtm` | Grafana LGTM startup and collector |
| `docker compose -f docs/run/compose/docker-compose.yml down -v` | Stop and **wipe** Postgres and LGTM data |

`start-app.sh` rebuilds images after code or **new** Flyway versions. Do not edit a migration that already ran: Flyway checksum-fails, Data Plane crash-loops, and Control Plane shows `Catalogue read failed (502)`. Recover with `docker compose -f docs/run/compose/docker-compose.yml down -v`, then `./docs/run/scripts/start-app.sh`. To reload seed without a new migration, use `./docs/run/scripts/seed-db.sh`.

### Check it is up

```bash
curl -sf localhost:3005/health && echo
curl -sf localhost:3007/health && echo
curl -sf localhost:3008/health && echo
curl -sf localhost:3009/health && echo
curl -sf localhost:3010/health && echo
```

Control Plane has no `/health`; open [http://localhost:3006](http://localhost:3006).

Grafana LGTM can take a minute. Wait until logs print `The OpenTelemetry collector and the Grafana LGTM stack are up and running.`, then open [http://localhost:3000](http://localhost:3000) (`admin` / `admin`).

### Dummy jobs and chats

Teaching job and chat-visible routes live under [`docs/run/dummy-jobs/`](docs/run/dummy-jobs/). Catalogue and flags: [docs/run/dummy-jobs/README.md](docs/run/dummy-jobs/README.md).

```bash
./docs/run/dummy-jobs/run-job.sh --list
./docs/run/dummy-jobs/run-job.sh --all
./docs/run/dummy-jobs/run-job.sh --mode 2
./docs/run/dummy-jobs/run-chat.sh --list
./docs/run/dummy-jobs/run-chat.sh --all
```

`--all` posts every row in `jobs.json` / `chats.json`. `--mode N` is one band (`0`–`3`). Both **only POST** unless you poll:

```bash
WAIT=1 ./docs/run/dummy-jobs/run-job.sh --all
WAIT=1 ./docs/run/dummy-jobs/run-chat.sh --all
```

One job (polls until done): `./docs/run/dummy-jobs/1-autonomous/fee_explain.sh` or `./docs/run/dummy-jobs/run-job.sh claims_adjudicate`. One chat: `./docs/run/dummy-jobs/chat/1-autonomous/fee_explain.sh`.

## Ports and URLs

| Port | What | URL |
| --- | --- | --- |
| 3000 | Grafana (LGTM) | http://localhost:3000 |
| 3005 | Front Door (channel API) | http://localhost:3005 |
| 3006 | Control Plane (catalogue UI) | http://localhost:3006 |
| 3007 | Data Plane | http://localhost:3007 |
| 3008 | Agent Runtime | http://localhost:3008 |
| 3009 | Capability Registry | http://localhost:3009 |
| 3010 | Tool mock (domain HTTP doubles) | http://localhost:3010 |
| 4317 | OTLP gRPC ingestion | http://localhost:4317 |
| 4318 | OTLP HTTP ingestion | http://localhost:4318 |
| 5432 | Postgres 16 | `fabric` / `fabric` |
| 8080 | Adminer | http://localhost:8080 |

Adminer: System **PostgreSQL**, server **`postgres`**, user/password **`fabric`**. Databases: `afd`, `adp`, `ar`, `acr`. There is no Control Plane database.

Grafana: username **`admin`**, password **`admin`**. Dev/demo only — not a production observability stack.

## Observability (Grafana LGTM)

Compose includes [`grafana/otel-lgtm`](https://hub.docker.com/r/grafana/otel-lgtm): one container with OpenTelemetry Collector, Prometheus (metrics), Loki (logs), Tempo (traces), and Grafana. Collector receives OTLP and Grafana already has the data sources.

**App services export OTLP** (Compose sets `OTEL_*` and Spring `MANAGEMENT_OTLP_*`). Service names: `agent-front-door`, `agent-data-plane`, `agent-runtime`, `agent-capability-registry`, `agent-control-plane`, `tool-mock`. Each depends on `otel-lgtm`.

Three-layer plan and tasks: [docs/tasks/observability-plan.md](docs/tasks/observability-plan.md), [docs/tasks/observability-todo.md](docs/tasks/observability-todo.md). Runbooks: [docs/run/runbooks/observability.md](docs/run/runbooks/observability.md).

Run Grafana with the fabric, or only the backend:

```bash
docker compose -f docs/run/compose/docker-compose.yml up otel-lgtm
```

### Send OpenTelemetry signals

From another Compose service, export to `otel-lgtm`:

| Transport | Endpoint |
| --- | --- |
| OTLP gRPC | `otel-lgtm:4317` |
| OTLP HTTP | `http://otel-lgtm:4318` |

From a process on the host (not in Compose), use `localhost:4317` or `http://localhost:4318`.

OpenTelemetry defaults to a 60s export interval. Compose sets `OTEL_METRIC_EXPORT_INTERVAL=500` for faster local demos.

### Correlation

| ID | Role | How to find it |
| --- | --- | --- |
| W3C `traceparent` | Distributed trace (Tempo) | Auto-propagated on RestClient / httpx |
| `X-Request-Id` | Edge request id (AFD mints or echoes) | Response header; span attr `request_id`; forwarded downstream |
| `correlation_id` | Run / jobs / freeze key (`corr-*`) | Span attr after Runtime start; jobs `202` body |
| `session_id` | Journey instance | Span attr; chat response body |
| `journey_id` | KPI bucket e.g. `chat.fee_explain` / `job.fee_explain` | Logs + `fabric_journey_outcome_total` |

Do not put utterance text, tokens, or stub claims in metric labels or span attributes.

### Layer map (local)

| Layer | What to look for |
| --- | --- |
| ① Business | JSON logs with `event` (`intent.decide.*`, `run.accepted`, `run.hydrate.*`, `run.completed`); counter `fabric_journey_outcome_total` |
| ② Service | Unbroken Tempo path AFD → ADP → AR → ACR → tool-mock; HTTP RED via Micrometer/OTel |
| ③ Infrastructure | Hikari/SQLAlchemy pool metrics; Compose labels `fabric.service` / `fabric.db` (`afd`/`adp`/`ar`/`acr`). Postgres exporter/cAdvisor deferred. |

### See a journey

Wait until LGTM logs print `The OpenTelemetry collector and the Grafana LGTM stack are up and running.` Generate a `fee_explain` turn, then confirm signals in Grafana ([http://localhost:3000](http://localhost:3000), `admin` / `admin`):

1. `./docs/run/dummy-jobs/1-autonomous/fee_explain.sh` or `./docs/run/dummy-jobs/chat/1-autonomous/fee_explain.sh`
2. Explore → **Loki**: `{service_name="agent-front-door"}` or `{service_name="agent-data-plane"}` — look for `run.accepted` / `intent.decide`
3. Explore → **Tempo**: `{.service.name="agent-front-door"}` — children include `agent-data-plane` and `agent-runtime` (Registry on hydrate; `tool-mock` and `llm.complete` / `tool.invoke` under `graph.invoke`). Search by the id you hold: `{.session_id="sess-…"}`, `{.correlation_id="corr-…"}`, or `{.request_id="req-…"}`.
4. Explore → **Prometheus**: `fabric_journey_outcome_total` or HTTP server duration for `agent-front-door`

Stdout JSON is a backup: `docker compose -f docs/run/compose/docker-compose.yml logs -f`.

To force a hydrate failure: POST a Runtime start body with a bad `route_version` (workload headers `Authorization: Bearer fabric-internal`, `X-Workload: afd`). Expect HTTP 422 `HYDRATE_FAILED`. Then Loki `run.hydrate.failed` with `reason_class` (no tokens or claims), Tempo `hydrate` span on `agent-runtime` with error status, and Prometheus `fabric_journey_outcome_total` with `outcome="hydrate_failed"`. Spot-check: no bearer tokens in Loki, no `X-Stub-Claims` JSON in span attributes, no full utterance as a metric label.

### Explore in Grafana

Log in at [http://localhost:3000](http://localhost:3000), then **Dashboards** or **Explore**.

**Metrics** (Prometheus / PromQL):

```promql
rate(http_server_request_duration_seconds_count[$__rate_interval])
```

```promql
fabric_journey_outcome_total
```

**Traces** (Tempo / TraceQL):

```traceql
{.service.name="agent-front-door"}
```

```traceql
{.correlation_id="corr-9f3c"}
```

```traceql
{.session_id="sess-88"}
```

```traceql
{.request_id="req-…"}
```

```traceql
{.service.name="agent-front-door" && .http.response.status_code=500}
```

**Logs** (Loki / LogQL) — services export OTLP logs to LGTM (also still print JSON to stdout):

```logql
{service_name="agent-front-door"}
```

```logql
{service_name="agent-runtime"} |= "run.hydrate"
```

```logql
{service_name="agent-front-door"} |= "run.accepted"
```

(Exact label may be `service_name` or `service_name` from OTel resource; if empty, use Grafana label browser on the Loki data source.)

After code changes that add log export, rebuild app images (`./docs/run/scripts/start-app.sh`) so the Logback/Python OTLP handlers are in the containers.
### Persistence

LGTM writes to `/data` in the container. Compose mounts named volume `lgtm-data`, so metrics, logs, traces, and Grafana state survive `down`. Only `docker compose -f docs/run/compose/docker-compose.yml down -v` deletes that volume (and Postgres).

## Components

```text
Chat / channel  →  Front Door :3005
                       │
                       ├─ decide / eligible / catalogue  →  Data Plane :3007
                       └─ start run                      →  Agent Runtime :3008
                                                              │
                                                              ├─ hydrate tools → Registry :3009
                                                              └─ invoke tools  → Tool mock :3010

Browser         →  Control Plane UI :3006  (reads Data Plane + Registry; does not decide)
Browser         →  Grafana :3000           (metrics, logs, traces via OTLP)
```

| Folder | Job | Stack | Database |
| --- | --- | --- | --- |
| [`agent-front-door`](agent-front-door/) | Channel ingress. Accepts the user turn, calls decide, starts the runtime. Chat JSON does not include `route_id` or `run_id`. | Java 21, Spring Boot, hexagonal | `afd` |
| [`agent-data-plane`](agent-data-plane/) | Routes, eligibility, keyword classify (`/v1/intent/*`), catalogue (`/v1/catalog/*`). Owns the route rows. Does **not** store decision audit. Only Front Door may call decide. | Java 21, Spring Boot, hexagonal | `adp` |
| [`agent-runtime`](agent-runtime/) | Executes the chosen route (hydrate tools, LangGraph loop). Nodes are built from the pinned tools and HTTP-call the mock. | Python 3.12, FastAPI, uv, LangGraph | `ar` |
| [`agent-capability-registry`](agent-capability-registry/) | Published capabilities and manifests (`id@version`). Runtime hydrates from here at pin. | Java 21, Spring Boot, hexagonal | `acr` |
| [`agent-control-plane`](agent-control-plane/) | Catalogue browser only. Lists routes, capabilities, prompts, manifests. **No** decide API, **no** database. | TypeScript, Node 22 | none |

Supporting pieces:

| Path | Role |
| --- | --- |
| [`docs/run/`](docs/run/) | Local run tree — folders only |
| [`docs/run/compose/`](docs/run/compose/) | Compose file, Postgres image, `.env.example` |
| [`docs/run/scripts/`](docs/run/scripts/) | start / stop / seed |
| [`docs/run/dummy-jobs/`](docs/run/dummy-jobs/) | Dummy jobs and chats for every teaching job route and chat-visible route (autonomy 0–3). Fresh ids each run |
| [`docs/run/seed/`](docs/run/seed/) | Catalogue SQL (teaching + lifecycle) |
| [`docs/run/tool-mock/`](docs/run/tool-mock/) | Config-driven domain HTTP doubles. Add a tool in `tools.json` (unique `method`+`path`), point the capability `invoke.url` at `http://tool-mock:3010{path}`, then rebuild |
| [`docs/contracts/`](docs/contracts/) | Frozen request/response fixtures and [stub auth](docs/contracts/stub-auth.md) |
| [`docs/`](docs/) | Architecture packs, [plan](docs/tasks/plan.md), and [future-enhancement.md](docs/future-enhancement.md) |

### Routes (v1)

Each route is versioned on its own (`route_id` + `route_version`). One version per route is `active`. Classify uses the active mix. A follow-up pin is that route’s id and version, not a shared table snapshot. A later contest-board snapshot is proposed in [docs/future-enhancement.md](docs/future-enhancement.md).

The catalogue seed is the Pattern 0–3 teaching set (29 routes, matching manifests, prompts, workflows, and Registry capabilities). IDs have no `v1`/`v3` suffix — version lives on `*_version` columns. `seed-db.sh` also loads extra published, draft, and retired cuts plus version history. Reload everything in one shot:

```bash
./docs/run/scripts/seed-db.sh
```

`seed-db.sh` deletes first, then inserts, so it is safe to run again. Each row has an `autonomy_mode` (0–3) from [Autonomy vs Control](https://jitendersharma.dev/insights/enterprise-ai-workflow-patterns-autonomy-vs-control). `fee_explain` needs claim `accounts:read` (stub user `jane`).

## Catalogue statuses

**Active** and **published** are not the same thing. Publishing freezes a version. Activating puts that version on the live contest board.

### Routes

Data Plane stores both a boolean `active` and a `status`. They stay in lockstep: `active=true` if and only if `status=active`. At most one version per `route_id` is active.

| Status | What it means |
| --- | --- |
| `draft` | Work in progress. Not in classify. |
| `published` | A released cut that is **not** the live contestant. |
| `active` | The one version of that route new chats classify against. |
| `retired` | Taken out of service. |

`GET /v1/catalog/routes` and `POST /v1/intent/decide` use **active** rows only. `GET /v1/catalog/routes?include=all` lists every cut. Control Plane tabs: Active, Published, Draft, Retired.

The teaching seed ships one `active` version per route (`2026.08.1`). Lifecycle seed adds extra published, draft, and retired cuts, including older versions for History.

### Capabilities, manifests, prompts

These catalogs do **not** store `active`. A published `(id, version)` is an immutable blob: a second `PUT` returns 409. Runtime hydrates the **pinned** version, never “whatever is live.”

| Status | Capabilities (Registry) | Manifests | Prompts (Data Plane) |
| --- | --- | --- | --- |
| `draft` | Editable. Agent Runtime cannot GET it. | Same in Registry (Runtime GET fails unless `published`). | Not the live pack. |
| `published` | Frozen. Runtime may hydrate it. | Frozen. Runtime hydrates `published` only. | Pack a route can point at. |
| `retired` / `deprecated` | `retired` in seed (architecture also uses `deprecated`). Runtime can still GET a retired capability by pin. | `retired` in Data Plane. | Prompts use `deprecated`. |

### Corpora

Routes keep `retrieval.scope` as corpus ids only (`["policy-engine"]`). No URL on the route. NAR looks up each id in Data Plane, then POSTs that row’s `url` (and `collection` when the gateway is shared).

`GET /v1/catalog/corpora` lists **published** rows. `GET /v1/catalog/corpora?include=all` includes `draft` / `deprecated`. `GET /v1/catalog/corpora/{corpus_id}` returns the row at any status. Runtime must POST only `published` rows. Two ids in scope are two GETs and two POSTs, then merge — never two indexes in one search call.

Control Plane maps the latest **published** capability or prompt onto the **Active** tab so the UI has one lifecycle. Older published versions show as Published. Both `deprecated` and `retired` show as Retired.

## Memory

Memory is **catalogue metadata**. A route either has a `dataplane.memory_profiles` row or it does not. Control Plane / `GET /v1/catalog/routes/{id}` expose it as `memory_profile`. Runtime honors **`working`** and **`loop`** on the run pin. **`conversation`** and **`long_term`** still need a Shared Memory box (not one of the four Fabric databases).

Author a profile only on routes that should remember something. Omit the row for one-shot LLM/jobs (`agent-chat`, `email_summarize`, `llm_pipeline`, `policy_memo`, `card_freeze`).

Seeded values: `session`, `none`, `checkpoint`, `retrieve_only`. Retrieval (`prefetch` / retrieve tools) is a **different** table — prefetch is not `long_term`.

### Where each type is stored

| Field | Save when | Prod store | Local Fabric DB |
| --- | --- | --- | --- |
| `working` | `working=session`, after each graph stage | Runtime run pin JSON | **`ar.runtime.runs.working`** |
| `loop` | `loop=checkpoint`, after each stage while the run is in flight | Same pin | **`ar.runtime.runs.checkpoint`** |
| `conversation` | `conversation=session`, after each chat turn | **Shared Memory** (session store), key `tenant/user/session_id` | **None.** Not `adp` / `ar` / `afd` / `acr`. Do not put transcripts on the run pin. |
| `long_term` | `long_term=retrieve_only`, after the run as recallable facts | **Shared Memory / RAG** (separate collection from conversation). Model sees it only via retrieve (or prefetch), never auto-injected | **None.** Same Shared box; still not a Fabric DB. |

`adp.dataplane.memory_profiles` is the **policy** (which types the route asked for), not the memories. `afd.frontdoor.freeze` (Redis in prod) is route stickiness, not conversation.

**Shared Memory (conversation + long_term):** a fifth store the architecture pack calls Shared. It is not built in this repo. Do not use Postgres `ar` for chat history or long-term facts — those outlive one `correlation_id` and must be isolated by tenant/user/session. Until Shared exists, those two fields are catalogue-only. Parked design: [docs/tasks/future-enhancement.md](docs/tasks/future-enhancement.md#shared-memory-conversation-and-long_term).

### Types

| Field | Values | Meaning | What you must build |
| --- | --- | --- | --- |
| `conversation` | `session` / `none` (omit) | Prior user/assistant turns in the next LLM call | Shared Memory session store (not built) |
| `working` | `session` / `none` | Scratch pad: tool hits, extracted fields, packed chunks | **Done.** Runtime writes `ar.runtime.runs.working` after each stage; `/turns` reloads `notes` |
| `loop` | `checkpoint` / `none` | Open-loop crash cursor (Pattern 1), not chat history | **Done.** Runtime writes `ar.runtime.runs.checkpoint` after each stage. Resume-from-step after a crash is still later |
| `long_term` | `retrieve_only` / `none` | Facts that must not sit in every prompt | Shared Memory / RAG (not built) |
| `ttl_hours` | `24` typical, `8` for KYC/dispute | When session/working blobs expire | Sweeper or store TTL. Freeze TTL is separate and shorter |
| `isolation` | `["tenant","user","session"]` | Key shape so Jane cannot see John | Namespace every read/write; stub has no tenant — key by `session_id` at minimum |

**`conversation=session`:** next utterance knows what was already said (`chat_session`, `policy_chat`, `fee_explain`). **`none` / omit:** each call is stateless (`email_summarize`, `llm_pipeline`).

**`working=session`:** later stages or a later turn keep intermediate artefacts. Cap size — not a transcript, not a corpus. Runtime flushes `notes` to `ar.runtime.runs.working` after each stage.

**`loop=checkpoint`:** the model may take several tool steps (`search_only`, `fraud_casefile`). Runtime writes `{step, stage_id, result, goal}` to `ar.runtime.runs.checkpoint` after each stage. **`none`:** fixed short pipeline (`chat_session`, `llm_pipeline`); death fails the run. Continuing the graph from that cursor after a replica crash is not wired yet.

**`long_term=retrieve_only`:** recall later via retrieve, not by stuffing history (`claims_adjudicate`, research/legal loops). **`none`:** nothing outlives the session window (`chat_session`, `kyc_onboarding`). Do not fake this by growing `conversation`. This is the Shared Memory box in the architecture pack.

### What to put on a route

| Route kind | `conversation` | `working` | `loop` | `long_term` |
| --- | --- | --- | --- | --- |
| One-shot LLM / job (`email_summarize`, `llm_pipeline`) | omit row | omit | omit | omit |
| Multi-turn chat, no tools (`chat_session`) | `session` | `session` | `none` | `none` |
| Chat + prefetch (`policy_chat`) | `session` | `session` | `none` | `none` |
| Open loop / guided with tools | `session` | `session` | `checkpoint` | `retrieve_only` |
| Sensitive packet (`kyc_onboarding`) | `session` | `session` | `checkpoint` | `none` + short TTL |

Enable in this order: (1) `conversation=session` on `chat_session` (needs Shared Memory), (2) `working` notes (Runtime, done), (3) `loop=checkpoint` writes (Runtime, done; crash-continue later), (4) `long_term` last (Shared Memory / RAG).

### Chat vs jobs

| | Chat (`/v1/assistant/*`) | Jobs (`/v1/jobs`) |
| --- | --- | --- |
| Session | Stable `session_id` (`sess-*`). Front Door freeze keeps the next turn on the same run (skip classify). That is **route stickiness**, not memory. | `session_id = job:{idempotency_key}`. One-shot. No follow-up turns. |
| Needs `conversation` | **Yes**, if the route has `conversation=session`. Prove it: turn 1 “my account is acc-42”, turn 2 “what was my account id?” | **No**, unless you add job follow-ups. Idempotent POST is not a second turn. |
| Needs `working` | Yes for multi-stage / multi-turn chat that must keep packed chunks or tool hits (`policy_chat`, `fee_explain`). | Yes **inside one job** if stages must see prior stage output. Persisted on `ar.runtime.runs.working` when the route profile says `session`. |
| Needs `loop` | Yes for Pattern 1 chat (`search_only`, `research_assistant`) so a crash does not restart the loop. | Same for long tool loops (`fraud_casefile`, `contract_review`). Irrelevant for `llm_pipeline` / `account_notify`. |
| Needs `long_term` | Only if a later **different** run should recall facts via retrieve. Ordinary chat should stay `none`. | Almost never for a fire-and-forget job. Use `retrieve_only` when the job writes facts another journey will look up. |
| Prove it | Two chat turns on `chat_session` with the same `session_id`. | One POST, poll to `completed`. Do not expect the next job to remember the last. |

Front Door freeze (`session_id` → `correlation_id` + route pin) is required for chat follow-ups. It does not load transcripts into the LLM. Jobs freeze exists so a duplicate idempotency key returns the same `correlation_id`; it is not conversation memory.

## Auth (stub)

Channel (humans → Front Door):

```http
Authorization: Bearer stub
X-Stub-Claims: {"sub":"jane","emts":{"accounts:read":true}}
```

Service-to-service: `Authorization: Bearer fabric-internal` and `X-Workload` of `afd` | `adp` | `acp` | `ar` | `acr`. Details: [contracts/stub-auth.md](docs/contracts/stub-auth.md).

## Docs

- [Intent](docs/intent/enterprise-agent-fabric-v1.md)
- [Architecture packs](docs/enterprise-agent-fabric-architecture/README.md)
- [Plan](docs/tasks/plan.md)
- [Future enhancements](docs/tasks/future-enhancement.md) (route table, Shared Memory)
