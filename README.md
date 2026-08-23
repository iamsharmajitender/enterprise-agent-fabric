# Enterprise Agent Fabric

Local fabric that **classifies a chat turn onto a route**, then runs that route. Five services, one Compose file, four Postgres databases. Kafka, IdP, and the LLM are stubbed.

Demo utterance: `"Why was I charged $42?"` → route `fee_explain` @ `2026.08.1` → `"Fee of $42 is the monthly account charge."`

Jobs path swimlane: [docs/run/diagrams/swimlane-jobs-fee-explain.html](docs/run/diagrams/swimlane-jobs-fee-explain.html) (`./docs/run/dummy-jobs/1-autonomous/fee_explain.sh`).

## Contents

- [Prerequisites](#prerequisites)
- [Run](#run)
  - [Check it is up](#check-it-is-up)
  - [Dummy jobs and chats](#dummy-jobs-and-chats)
- [Evals](#evals)
- [Ports and URLs](#ports-and-urls)
- [Observability (Grafana LGTM)](#observability-grafana-lgtm)
  - [Send OpenTelemetry signals](#send-opentelemetry-signals)
  - [Correlation](#correlation)
  - [Layer map (local)](#layer-map-local)
  - [See a journey](#see-a-journey)
  - [Explore in Grafana](#explore-in-grafana)
  - [Persistence](#persistence)
- [Components](#components)
- [The four boxes (AFD, ADP, ACR, AR)](#the-four-boxes-afd-adp-acr-ar)
  - [AFD — Agent Front Door](#afd--agent-front-door-afd-3005)
  - [ADP — Agent Data Plane](#adp--agent-data-plane-adp-3007)
  - [ACR — Agent Capability Registry](#acr--agent-capability-registry-acr-3009)
  - [AR — Agent Runtime](#ar--agent-runtime-ar-3008)
  - [How README topics map onto the four boxes](#how-readme-topics-map-onto-the-four-boxes)
- [Routes (v1)](#routes-v1)
- [Catalogue statuses](#catalogue-statuses)
  - [Routes](#routes)
  - [Capabilities, manifests, prompts](#capabilities-manifests-prompts)
  - [Corpora](#corpora)
- [Workflows](#workflows)
  - [Stage fields](#stage-fields)
  - [How Runtime hydrates a workflow](#how-runtime-hydrates-a-workflow)
  - [What workflow to put on a route](#what-workflow-to-put-on-a-route)
- [Prompts](#prompts)
  - [Pack shape](#pack-shape)
  - [What prompt to put on a route](#what-prompt-to-put-on-a-route)
- [Retrieve](#retrieve)
  - [Modes](#modes)
  - [Corpus rows](#corpus-rows)
  - [What retrieval to put on a route](#what-retrieval-to-put-on-a-route)
- [Tools](#tools)
  - [Manifest vs capability](#manifest-vs-capability)
  - [Kinds](#kinds)
  - [How the loop calls them](#how-the-loop-calls-them)
  - [What manifest to put on a route](#what-manifest-to-put-on-a-route)
- [Memory](#memory)
  - [Where each type is stored](#where-each-type-is-stored)
  - [Types](#types)
  - [What to put on a route](#what-to-put-on-a-route)
  - [Chat vs jobs](#chat-vs-jobs)
- [Auth (stub)](#auth-stub)
- [Docs](#docs)

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
| `./docs/run/scripts/seed-db.sh` | Delete and reload catalogue + lifecycle seed |
| `docker compose -f docs/run/compose/docker-compose.yml ps` | Process status |
| `docker compose -f docs/run/compose/docker-compose.yml logs -f` | Follow all logs |
| `docker compose -f docs/run/compose/docker-compose.yml logs -f agent-data-plane` | One service |
| `docker compose -f docs/run/compose/docker-compose.yml logs -f otel-lgtm` | Grafana LGTM startup and collector |
| `docker compose -f docs/run/compose/docker-compose.yml down -v` | Stop and **wipe** Postgres and LGTM data |

`start-app.sh` rebuilds images after code or **new** Flyway versions. Do not edit a migration that already ran: Flyway checksum-fails, Data Plane crash-loops, and Control Plane shows `Catalogue read failed (502)`. Recover with `docker compose -f docs/run/compose/docker-compose.yml down -v`, then `./docs/run/scripts/start-app.sh`. Squashing Flyway history into a new `V1` is the same: wipe the Postgres volume so `flyway_schema_history` is empty. To reload seed without a new migration, use `./docs/run/scripts/seed-db.sh`.

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

Seed job and chat-visible routes live under [`docs/run/dummy-jobs/`](docs/run/dummy-jobs/). Catalogue and flags: [docs/run/dummy-jobs/README.md](docs/run/dummy-jobs/README.md).

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

## Evals

CI-gated routing and pin checks for the catalogue seed. They are **not** on decide / pin / start / loop — Jane’s turn does not run them. A failed eval blocks a catalogue change (or a PR), not a live reply.

Golden sets live next to Data Plane tests, not under `docs/` (that tree is the operator scratchpad):

```text
agent-data-plane/src/test/resources/eval/
  routing-golden.json       # chat contest + adversarial rows
  jobs-entitle-golden.json  # named route_id + claims (no classify)
  case.schema.json
  example-chat-route.json
```

`eval_suite_id` on a route is slice 3 (route quality, not landed). Empty is correct for free-form chat. Routing is the **board** (the labelled mix in the JSON header), not a pointer on one row.

### What CI runs

There is no GitHub Actions workflow in this repo yet. The hook is Data Plane `mvn test` (also the ADP image build, which already runs `mvn test`). That includes:

| Suite | Question |
| --- | --- |
| `RoutingEvalTest` | Chat: utterance + claims + channel → `route` / `clarify` / `abstain` |
| `JobsEntitleEvalTest` | Jobs: named `route_id` + claims → `route` or fail-closed `abstain` |
| `CataloguePinLintTest` | Every active row can pin: pointers resolve, Pattern 0 has no tools/workflow, high-risk writes still have a workflow |

```bash
./agent-data-plane/run-eval.sh
# same as:
cd agent-data-plane && mvn test -Dtest=RoutingEvalTest,JobsEntitleEvalTest,CataloguePinLintTest
```

Flip one `expected.route_id` in `routing-golden.json` and the gate must go red. Restore it. Do not delete an incident case to go green.

### What CI does not run

Dummy `--all` needs a running stack. It is pin/hydrate smoke, **not** the routing labels.

```bash
WAIT=1 ./docs/run/dummy-jobs/run-job.sh --all
```

`WAIT=1` polls until `completed` and exits non-zero on `failed` or timeout.

Plan / task list: [docs/tasks/eval-plan.md](docs/tasks/eval-plan.md), [docs/tasks/eval-todo.md](docs/tasks/eval-todo.md). Slice 3 (`eval_suite_id` tool-order / citations) is later.

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
2. Explore → **Loki**: `{service_name=~"agent-front-door|agent-data-plane|agent-runtime"} | session_id="sess-…"` (field filter — the line body is only `run.accepted`, so `|= "sess-…"` is empty). Look for `run.accepted` / `intent.decide`
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

```logql
{service_name=~"agent-front-door|agent-data-plane|agent-runtime"} | session_id="sess-f71adfd75ad0"
```

(Exact label may be `service_name` from the OTel resource; if empty, use Grafana label browser on the Loki data source.)

Logs keep a single OTel pair `trace_id` / `span_id` (not Brave `traceId` / `spanId`). Resource does not include `telemetry.sdk.*`.

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

What each box owns, how a turn/job flows, and how [Routes](#routes-v1), [Catalogue](#catalogue-statuses), [Workflows](#workflows), [Prompts](#prompts), [Retrieve](#retrieve), [Tools](#tools), [Memory](#memory), and [Auth](#auth-stub) map onto them: [The four boxes (AFD, ADP, ACR, AR)](#the-four-boxes-afd-adp-acr-ar).

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
| [`docs/run/dummy-jobs/`](docs/run/dummy-jobs/) | Dummy jobs and chats for every seed job route and chat-visible route (autonomy 0–3). Fresh ids each run |
| [`docs/run/seed/`](docs/run/seed/) | Catalogue SQL (seed + lifecycle) |
| [`docs/run/tool-mock/`](docs/run/tool-mock/) | Config-driven domain HTTP doubles. Add a tool in `tools.json` (unique `method`+`path`), point the capability `invoke.url` at `http://tool-mock:3010{path}`, then rebuild |
| [`docs/README.md`](docs/README.md) | Documentation map (start / understand / catalogue / architecture / reference) |
| [`docs/04-architecture/`](docs/04-architecture/) | Architecture packs |
| [`docs/05-reference/`](docs/05-reference/) | Frozen request/response fixtures and [stub auth](docs/05-reference/stub-auth.md) |
| [`docs/`](docs/) | [plan](docs/tasks/plan.md), [evals](docs/tasks/eval-plan.md), [intent router](docs/tasks/intent-plan.md), and [future-enhancement.md](docs/tasks/future-enhancement.md) |

## The four boxes (AFD, ADP, ACR, AR)

Four services, four Postgres databases. **Control Plane** (`:3006`) is a fifth process with **no** database — a catalogue browser only. It is not AFD/ADP/ACR/AR.

Request order is **AFD → ADP (classify / pin pointers) → AR (run) → ACR (hydrate at pin)**. Channels never dial ADP, AR, or ACR.

How the later README topics land on each box is summarized at the end of this section.

### AFD — Agent Front Door (`afd`, :3005)

**What.** The only public ingress. Chat (`/v1/assistant/*`) and jobs (`/v1/jobs`) share this process locally. Chat JSON does not include `route_id` or `run_id`; jobs callers **do** name `route_id`. AFD entitles, freezes, starts Runtime, and fans status back. It does **not** classify, store the catalogue, hydrate tools, or run the loop.

**How.**

1. Channel auth: `Authorization: Bearer stub` + `X-Stub-Claims`. Missing bearer → 401.
2. **Jobs:** `POST /v1/jobs` with explicit `route_id` + `idempotency_key`. Skip keyword classify and `clarify`. Still call Data Plane decide (`ingress: "jobs"`) so entitle + record happen. Missing claims / unknown route → **403**, do not start Runtime.
3. **Chat:** `POST /v1/assistant/turns` with a message (or opaque `hint_id` / `option_id`). Data Plane classifies. Only `outcome=route` freezes and starts. `clarify` / `abstain` never pin.
4. On `route`, AFD GETs the pinned catalogue row, writes a **freeze** keyed by `session_id` (`sess-*` for chat, `job:{idempotency_key}` for jobs), then `POST /v1/runs` on Runtime. Returns `202 { "correlation_id" }`. AFD never mints that id — if Runtime fails, AFD returns **503**.
5. Status: `GET /v1/jobs/{correlation_id}` (or chat events) polls Runtime HTTP. **No** Data Plane call on the poll path.
6. Follow-up chat turns reuse the freeze (same pin, skip classify). Duplicate job keys return the original `correlation_id`.

**Database `afd`.** Schema `frontdoor`. Freeze is route stickiness (`session_id` → pin + `correlation_id`), not conversation memory. Local jobs freeze is in-memory until the chat-path table; prod is Redis/Valkey. Outbound workload: `Authorization: Bearer fabric-internal`, `X-Workload: afd`.

Pack: [agent-front-door](docs/04-architecture/agent-front-door.md). Service notes: [`agent-front-door/README.md`](agent-front-door/README.md).

### ADP — Agent Data Plane (`adp`, :3007)

**What.** Catalogue and classify. Owns route rows, eligibility, keyword decide, prompts, workflows, corpora, and **memory_profile policy**. Serves `GET /v1/catalog/*` and `POST /v1/intent/decide`. Does **not** pin, start Runtime, mint `correlation_id`, store decision audit, or hold transcripts.

**How.**

1. Only AFD may call decide. Control Plane and Runtime must not.
2. Decide = **active** routes ∩ `required_claims` ∩ channel, then layers. Chat may keyword-classify (Layer ②). Jobs bind Layer ① (`route_id` already set) — they still entitle; they never get `clarify`.
3. Outcomes: `route` / `clarify` / `abstain`. Only `route` is startable, and **AFD** starts AR.
4. Catalogue APIs return pointers at a version: `tool_manifest`, policy, model, `memory_profile`, `activation_target`, `agent_client_id`. Classify uses the **active** mix. A follow-up pin is that route’s `route_id` + `route_version`, not “whatever is live now.”
5. Runtime (and AFD after `route`) **GET** the pinned row. Runtime does not load `active` and does not classify.
6. `memory_profiles` and `retrieval` are sibling tables on the route. Retrieval/prefetch is **not** `long_term`.

**Database `adp`.** Schema `dataplane`. Policy lives here; memories do not. A down catalogue fails closed (no new starts). A down Runtime does not stop classify.

Pack: [agent-plane](docs/04-architecture/agent-plane.md) (Data Plane half; ACP is the UI + future audit).

### ACR — Agent Capability Registry (`acr`, :3009)

**What.** Published capabilities and manifests as immutable `id@version`. Publishers append; route rows only **point** at a `tool_manifest`. Runtime hydrates the whole pinned manifest **once at pin**, then the loop never calls this box. Not a third AFD, not MCP `list_tools`, not permission.

**How.**

1. `PUT /v1/capabilities/{id}/versions/{version}` and `PUT /v1/manifests/...` append a cut. A second `PUT` of a published version is **409**.
2. Runtime `GET`s the pinned manifest, then each capability ref, **before** the LLM. Mid-loop registry GET is forbidden. If hydrate fails, Runtime returns **422** `HYDRATE_FAILED` and AFD does not invent a run.
3. Two kinds, one catalog: `domain` (HTTP to tool-mock / a real API) and `agent` (child job via AFD, not a POST to the callee AR).
4. Control Plane lists capabilities/manifests for humans. Chat never sees this catalog as JSON.
5. Status: Runtime may hydrate `published` (and still GET a retired pin). `draft` is not hydratable.

**Database `acr`.** Append-only versions. If ACR dies, **new** runs cannot hydrate; in-flight pins already have schemas on the run pin.

Pack: [agent-capability-registry](docs/04-architecture/agent-capability-registry.md).

### AR — Agent Runtime (`ar`, :3008)

**What.** Does the work. Copies the freeze into a durable **run pin**, hydrates tools from ACR, runs the LangGraph loop (Patterns 0–3), invokes tools (local: tool-mock :3010). Does **not** classify the next utterance, own agent identity, or store conversation / long-term facts.

**How.**

1. Only AFD starts AR (`POST /v1/runs`, `mode: new`). Returns `202 { "correlation_id" }` (`corr-*`). Default start is async.
2. Hydrate: GET pinned catalogue row from ADP → GET manifest + capabilities from ACR → freeze those schemas on the pin. Then run.
3. Graph nodes come from the pinned tools (or workflow/prompt if there is no manifest). HTTP invoke goes to the capability `invoke.url` (Compose: `http://tool-mock:3010...`).
4. Memory it **does** honor, from the catalogue `memory_profile`:
   - `working=session` → `ar.runtime.runs.working` (`notes`) after each stage; `/v1/runs/{id}/turns` reloads them
   - `loop=checkpoint` → `ar.runtime.runs.checkpoint` (`step`, `stage_id`, `result`, `goal`). Resume-from-step after a crash is not wired yet
5. Memory it **does not** honor yet: `conversation` and `long_term` stay catalogue-only until Shared Memory / RAG exists. Do not write either onto this pin.
6. `GET /v1/runs/{correlation_id}` is slim status for AFD poll. `GET /v1/runs?session_id=` is open-run when AFD freeze TTL misses. Duplicate `idempotency_key` returns the original id.

**Database `ar`.** Schema `runtime`. Run pin is authoritative for the loop (longer than freeze TTL). Shared Memory is a fifth store, not this database.

Pack: [agent-runtime](docs/04-architecture/agent-runtime.md).

### How README topics map onto the four boxes

| Topic in this README | AFD | ADP | ACR | AR |
| --- | --- | --- | --- | --- |
| [Ports](#ports-and-urls) | `:3005` public chat + jobs | `:3007` private | `:3009` private | `:3008` private |
| [Observability](#observability-grafana-lgtm) | Mints/echoes `X-Request-Id`; `run.accepted`; journey `chat.*` / `job.*` | `intent.decide.*` | Hydrate GETs on the Tempo path | `run.hydrate.*`, `run.started` / `completed`; span attrs `correlation_id` |
| [Routes](#routes-v1) | Freezes the pin AFD got from decide; jobs name `route_id` | Owns versioned rows; classify = **active** mix | Manifest pointer only — no `tools[]` on the route | Executes the **pinned** version; never re-reads `active` |
| [Catalogue statuses](#catalogue-statuses) | After `route`, GET that version | `active` vs `published` vs `draft` / `retired` on routes; prompts/workflows/corpora | Capability + manifest `draft` / `published` / `retired`; hydrate `published` | Hydrates the pin; 422 if the cut is missing or still draft |
| [Workflows](#workflows) | None. Pin already has `workflow_id` on the row | Owns `dataplane.workflows` (stages, `llm_role`, allowlist). Route points at `workflow_id` | None | Hydrate: with a manifest, stamp `llm_role` onto tools; without, one graph node per stage. Graph is still linear — `branch` / `human_gate` are catalogue-only |
| [Prompts](#prompts) | None | Owns `dataplane.prompt_packs` + `prompt_role_templates`. Route points at `prompt_id` | None | GET published pack; `host` plus `by_llm_role` text onto each node. LLM stub / Ollama uses that string |
| [Retrieve](#retrieve) | None | Owns `dataplane.retrieval` (mode + corpus ids) and `dataplane.corpora` (url / collection) | Retrieve tools are ordinary capabilities (`clause_search`, `account_fee_lookup`) | Does **not** POST the corpus gateway yet. Prefetch stages with empty `invoke` are no-ops. Retrieve **tools** HTTP-call tool-mock like any other tool |
| [Tools](#tools) | None. Does not inline `tools[]` | Route stores `tool_manifest` + version; ADP copy is for the catalogue UI | Source of truth: published manifest + each `id@version` (schema, `invoke.url`, `kind`) | Hydrate whole manifest before the LLM. Loop HTTP-calls `invoke.url` (local: tool-mock). No mid-loop registry GET |
| [Memory](#memory) | Freeze = stickiness, not transcripts. Chat `session_id` vs jobs `job:{key}` | `dataplane.memory_profiles` is **policy** (`conversation`, `working`, `loop`, `long_term`, TTL, isolation) | None | Honors `working` + `loop` on the pin. Ignores `conversation` / `long_term` until Shared exists |
| [Auth (stub)](#auth-stub) | Channel bearer in; workload `afd` out | Workload `afd` on decide; `ar` / `acp` on catalogue GET | Workload `ar` on hydrate GET; `acp` on UI list | Workload `afd` on start; does not use the user bearer as tool `Authorization` |

Three routers stay separate: **ADP** picks the workflow/manifest, **AR** picks the next tool/step, the **model router** (inside AR) picks the LLM. Do not collapse them.

## Routes (v1)

Each route is versioned on its own (`route_id` + `route_version`). One version per route is `active`. Classify uses the active mix. A follow-up pin is that route’s id and version, not a shared table snapshot. A later contest-board snapshot is proposed in [docs/tasks/future-enhancement.md](docs/tasks/future-enhancement.md).

The catalogue seed is the Pattern 0–3 set (31 routes, matching manifests, prompts, workflows, and Registry capabilities). IDs have no `v1`/`v3` suffix — version lives on `*_version` columns. `seed-db.sh` also loads extra published, draft, and retired cuts plus version history. Reload everything in one shot:

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

The catalogue seed ships one `active` version per route (`2026.08.1`). Lifecycle seed adds extra published, draft, and retired cuts, including older versions for History.

### Capabilities, manifests, prompts

These catalogs do **not** store `active`. A published `(id, version)` is an immutable blob: a second `PUT` returns 409. Runtime hydrates the **pinned** version, never “whatever is live.” What they are: [Tools](#tools), [Prompts](#prompts).

| Status | Capabilities (Registry) | Manifests | Prompts (Data Plane) |
| --- | --- | --- | --- |
| `draft` | Editable. Agent Runtime cannot GET it. | Same in Registry (Runtime GET fails unless `published`). | Not the live pack. |
| `published` | Frozen. Runtime may hydrate it. | Frozen. Runtime hydrates `published` only. | Pack a route can point at. |
| `retired` / `deprecated` | `retired` in seed (architecture also uses `deprecated`). Runtime can still GET a retired capability by pin. | `retired` in Data Plane. | Prompts use `deprecated`. |

### Corpora

Routes keep `retrieval.scope` as corpus ids only (`["policy-engine"]`). No URL on the route. How prefetch vs retrieve-tool works: [Retrieve](#retrieve). NAR looks up each id in Data Plane, then POSTs that row’s `url` (and `collection` when the gateway is shared).

`GET /v1/catalog/corpora` lists **published** rows. `GET /v1/catalog/corpora?include=all` includes `draft` / `deprecated`. `GET /v1/catalog/corpora/{corpus_id}` returns the row at any status. Runtime must POST only `published` rows. Two ids in scope are two GETs and two POSTs, then merge — never two indexes in one search call.

Control Plane maps the latest **published** capability or prompt onto the **Active** tab so the UI has one lifecycle. Older published versions show as Published. Both `deprecated` and `retired` show as Retired.

## Workflows

A workflow is a **fixed stage list**. Pattern 2 (deterministic) and Pattern 3 (guided) point a route at `workflow_id`. The model does not invent the next stage. Open-loop Pattern 1 routes (`fee_explain`, `search_only`) omit the workflow and loop tools instead.

**AFD** never reads workflows. **ADP** owns `dataplane.workflows` and exposes `GET /v1/catalog/workflows`. The route row stores only `workflow_id` (no version pin). Runtime then GETs `/v1/catalog/workflows/{id}` — the **latest** cut, not a frozen version. **ACR** is not involved. **AR** uses the document at hydrate.

### Stage fields

| Field | Meaning |
| --- | --- |
| `id` | Stage name (`extract`, `clause_search`, `memo`) |
| `tool` | Manifest tool / capability id this stage binds (`ocr_extract`). Omit on LLM-only or prefetch stages |
| `llm_role` | `none` / `query_formulation` / `classify` / `synthesis` — see [Prompts](#prompts) |
| `corpus` | Corpus id for a named retrieve stage (`clause-index`). Not a URL |
| `allowlist` | Pattern 3: tools the model may pick **inside** this stage |
| `branch` | Catalogue branch (`high` → `manual_review`). Not executed yet |
| `type` | e.g. `human_gate`. Catalogue-only today |
| `side_effect` / `requires_approval` | Gated writes (`freeze_card`). Catalogue-only today |

Seeded examples: `llm_pipeline` (three LLM stages, no tools), `card_freeze` (identity → limits → freeze), `msa_risk_review` (OCR → two retrieve stages → score → memo).

### How Runtime hydrates a workflow

1. **Route has `tool_manifest`:** ACR hydrates every capability on the manifest. Workflow only **stamps** `llm_role` (and therefore prompt text) onto tools whose id matches `stage.tool`. Graph order is manifest order, not stage order.
2. **Route has no manifest:** one graph node per stage. `invoke` is empty, so `llm_role=none` stages (typical `prefetch`) skip HTTP; `classify` / `synthesis` call the LLM.
3. The local LangGraph is **linear**. `branch`, `human_gate`, stage `allowlist`, and approval flags are stored on ADP and shown in Control Plane; AR does not walk them yet.

If hydrate finds neither a manifest, a workflow, nor a prompt: **422** `HYDRATE_FAILED`.

### What workflow to put on a route

| Route kind | `workflow_id` |
| --- | --- |
| Pattern 0 one-shot (`email_summarize`, `chat_session`) | omit |
| Pattern 1 open loop (`fee_explain`, `search_only`) | omit — `max_loop_steps` instead |
| Pattern 2 fixed pipeline (`llm_pipeline`, `card_freeze`, `msa_risk_review`) | required |
| Pattern 3 guided (`ticket_triage`, `contract_review`) | required, stages carry `allowlist` |

## Prompts

A prompt pack is the **text the LLM sees**, not the route description. Pattern 0 can be prompt-only. Tool and workflow routes still point at a pack so each `llm_role` has a template.

**AFD** does not load packs. **ADP** owns `dataplane.prompt_packs` (`host`, `status`, `owner`) and `dataplane.prompt_role_templates` (`llm_role`, `task_type`, `text`). APIs: `GET /v1/catalog/prompts`. The route stores `prompt_id` only. Runtime GETs `/v1/catalog/prompts/{id}` (published pack). **ACR** is not involved. **AR** copies `host` / role text onto hydrated nodes as `llm_prompt`.

Status: `draft` / `published` / `deprecated` — no `active`. One published version per `prompt_id`. Lifecycle: [Catalogue statuses](#capabilities-manifests-prompts).

### Pack shape

| Piece | Where | Used when |
| --- | --- | --- |
| `host` | `prompt_packs.host` | System-level instruction. Prompt-only routes (no workflow) use `host` as the single `synthesis` node |
| `by_llm_role.{role}.text` | `prompt_role_templates` | Stamped onto the matching workflow stage / tool |
| `task_type` | `plan` / `synthesize` / `classify` | Labels the template; must not be `none` |

`llm_role` on a **stage** (or stamped on a tool) is what Runtime executes:

| `llm_role` | Graph | Example |
| --- | --- | --- |
| `none` | HTTP if `invoke.url` is set; otherwise no-op (prefetch placeholder) | `ocr_extract`, `notify_customer`, `prefetch` |
| `query_formulation` | LLM writes `payload.query`, then HTTP | `msa_risk_review` retrieve stages |
| `classify` / `synthesis` | LLM only; skip HTTP | `llm_pipeline` extract / rewrite; memo stages |

Unknown roles fail the run. LLM-only roles need the Runtime LLM (local Ollama). Tool-only `none` stages finish against tool-mock without a model.

### What prompt to put on a route

| Route kind | Prompt |
| --- | --- |
| Prompt-only (`agent-chat`, `email_summarize`, `chat_session`) | Pack with `host`. No role templates required |
| Prefetch then generate (`policy_memo`, `policy_chat`) | `host` plus `synthesis` template that says to use packed chunks |
| Open loop with tools (`fee_explain`) | `host` (“use the fee lookup tool; do not invent charges”) |
| Workflow with mixed stages (`msa_risk_review`) | `host` plus `query_formulation` and `synthesis` templates |
| Pure write path (`account_notify`, `card_freeze`) | omit — `llm_role` is `none` on every stage |

Do not grow the prompt into a transcript. That is [Memory](#memory) `conversation`, not this pack.

## Retrieve

Retrieval is **corpus policy** on the route, not long-term memory and not a tool list. Prefetch is not `long_term`. A retrieve **tool** is still a [capability](#tools) (`clause_search`, `account_fee_lookup`).

**AFD** does not retrieve. **ADP** owns `dataplane.retrieval` (`mode`, `scope` = corpus ids) and `dataplane.corpora` (display name, `url`, `collection`, auth, owner, status). `GET /v1/catalog/corpora`. The route never stores a retrieve URL. **ACR** publishes retrieve tools like any other `kind=domain` capability. **AR** does not GET corpora or POST the retrieve gateway yet. Prefetch is catalogue + a no-op stage. A retrieve tool on the manifest is ordinary HTTP to tool-mock.

### Modes

Omit the `retrieval` row when the route must not touch an index (`email_summarize`, `llm_pipeline`, `chat_session`, `search_only` — web tools are not corpus RAG).

| `retrieval.mode` | Who searches | Model can skip? | Seeded routes |
| --- | --- | --- | --- |
| `deterministic_prefetch` | App packs `scope` corpora **before** generate | No | `policy_chat`, `policy_memo`, `fraud_casefile`, `pack_then_review`, `product_explain` |
| `tool` | Named retrieve stages / tools over `scope` | Only if the workflow lets the model skip that stage (Pattern 1/3) | `fee_explain` (`accounts`), `msa_risk_review` (`clause-index`, `legal-playbook`), `kyc_onboarding` |
| `none` / omit | — | — | One-shot LLM, open web-search loops |

`scope` is one or more corpus ids. Two ids ⇒ two lookups, then merge — never two indexes in one search call. Workflow `stage.corpus` names which index a **named** retrieve stage uses; it must be in `scope`.

### Corpus rows

| Field | Role |
| --- | --- |
| `corpus_id` | What `scope` and `stage.corpus` point at (`policy-engine`, `clause-index`) |
| `url` | Retrieve gateway (`https://retrieve.internal/v1/search` in seed). Not on the route |
| `collection` | Index name when the gateway is shared |
| `status` | `draft` / `published` / `deprecated`. Runtime must use **published** only (when POST is wired) |

Designed (not in this Runtime): look up each id, POST `url` with `collection`, pack chunks into working memory / the generate prompt. Until then, prefetch stages with empty `invoke` skip HTTP (`policy_memo`), and retrieve tools hit tool-mock (`fee_explain` → `POST http://tool-mock:3010/fees/explain`).

### What retrieval to put on a route

| Route kind | Retrieve |
| --- | --- |
| No index (`email_summarize`, `llm_pipeline`, `search_only`) | omit row |
| Grounded chat / memo, model must not skip (`policy_chat`, `policy_memo`) | `deterministic_prefetch` + corpus ids |
| Open loop with one retrieve tool (`fee_explain`) | `tool` + `["accounts"]`; tool is on the manifest |
| Fixed retrieve stages (`clause_lookup`, `msa_risk_review`) | `tool` + scope; workflow stages set `tool` + `corpus` |

## Tools

The route has **no** `tools[]`. It points at `tool_manifest` + `tool_manifest_version`. Publishers append immutable capabilities; the manifest **refers** (`capability_id` + `capability_version`). Runtime hydrates the whole pin **before** the LLM. The loop never calls the registry again.

**AFD** does not hydrate. **ADP** stores the pointer on the route and keeps a catalogue copy of manifests for Control Plane (`GET /v1/catalog/manifests`). **ACR** is the hydrate source of truth: `GET /v1/manifests/{id}/versions/{version}`, then each `GET /v1/capabilities/{id}/versions/{version}`. **AR** freezes schemas + `invoke` on the run pin, then HTTP-calls `invoke.url` (Compose: tool-mock `:3010`).

A published capability is not permission. `pdp_action` / `risk_tier` sit on the manifest ref (agent policy). Dual check in Shared PEP is not built locally.

### Manifest vs capability

| Object | Who writes | Holds |
| --- | --- | --- |
| Capability `id@version` | Publisher (`PUT` ACR) | `kind`, schemas, `invoke` (`method`, `url`, `auth`), snippet, owner, status |
| Tool manifest `id@version` | Agent developer | List of refs: `name`, `capability_id`, `capability_version`, `pdp_action`, `risk_tier` |
| Route row | Platform | `tool_manifest` + `tool_manifest_version` only |

Publish is append-only. A second `PUT` of a published version is **409**. Runtime hydrates `published` (a retired pin can still GET). `draft` is not hydratable. Mid-loop `list_tools` is forbidden.

### Kinds

| `kind` | `invoke` | Local |
| --- | --- | --- |
| `domain` | Domain HTTP (`http://tool-mock:3010/fees/explain`) | Tools in [`docs/run/tool-mock/`](docs/run/tool-mock/) |
| `agent` | API AFD jobs (`POST /v1/jobs` with callee `route_id`) | Not the callee AR. LLM never sees `{jobs_url}` or `activation_target` |

Do not add kinds for retrieve, prompts, workflows, memory, or MCP. Contract: [`docs/02-understand/capabilities.md`](docs/02-understand/capabilities.md).

Add a domain tool: unique `method`+`path` in `tools.json`, point the capability `invoke.url` at `http://tool-mock:3010{path}`, rebuild.

### How the loop calls them

1. Hydrate fails closed (422) if the pinned manifest or any ref is missing.
2. Each hydrated record becomes one LangGraph node, in manifest order. Workflow `llm_role` / prompt text are stamped when `stage.tool` matches capability id.
3. `invoke.url` set + `llm_role=none` → HTTP. `query_formulation` → LLM then HTTP. `classify` / `synthesis` → LLM, skip HTTP even if a url exists.
4. Telemetry: span `tool.invoke` (no tokens, no claims). Tempo path includes ACR on hydrate and tool-mock on invoke.

Pattern 0 **cannot** take tools. `account_notify` / `card_freeze` take a manifest **and** a workflow (`llm_role=none`). Pattern 1 takes a manifest and `max_loop_steps`, no workflow.

### What manifest to put on a route

| Route kind | Manifest |
| --- | --- |
| Prompt-only / LLM pipeline (`email_summarize`, `llm_pipeline`, `policy_memo`) | omit — hydrate from workflow and/or prompt |
| One tool (`fee_explain`, `account_notify`, `clause_lookup`) | Manifest with one ref |
| Multi-tool loop or pipeline (`fraud_casefile`, `card_freeze`, `msa_risk_review`) | Manifest with every tool the stages need |
| Child Legal run | Parent manifest has `kind=agent` (`start_contract_review`); do not POST the callee AR |

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

Service-to-service: `Authorization: Bearer fabric-internal` and `X-Workload` of `afd` | `adp` | `acp` | `ar` | `acr`. Details: [stub-auth.md](docs/05-reference/stub-auth.md).

## Docs

- [Documentation map](docs/README.md) (start / understand / catalogue / architecture / reference)
- [The four boxes](#the-four-boxes-afd-adp-acr-ar) (this README — AFD, ADP, ACR, AR)
- [Workflows](#workflows), [Prompts](#prompts), [Retrieve](#retrieve), [Tools](#tools)
- [Intent](docs/intent/enterprise-agent-fabric-v1.md)
- [Architecture packs](docs/04-architecture/README.md)
- [Plan](docs/tasks/plan.md)
- [Evals](#evals) — [eval-plan.md](docs/tasks/eval-plan.md) / [eval-todo.md](docs/tasks/eval-todo.md) (routing golden set — not on the hot path)
- [Intent router](docs/tasks/intent-plan.md) / [intent-todo.md](docs/tasks/intent-todo.md) (layered classifier ①–③)
- [Observability](docs/tasks/observability-plan.md) / [observability-todo.md](docs/tasks/observability-todo.md)
- [Future enhancements](docs/tasks/future-enhancement.md) (route table, Shared Memory)
