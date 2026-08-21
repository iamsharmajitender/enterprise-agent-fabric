# Enterprise Agent Fabric

Local fabric that **classifies a chat turn onto a route**, then runs that route. Five services, one Compose file, four Postgres databases. Kafka, IdP, and the LLM are stubbed.

Demo utterance: `"Why was I charged $42?"` → route `fee_explain` @ `2026.08.1` → `"Fee of $42 is the monthly account charge."`

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- From the **repository root** for every command below

## Run

```bash
./docs/run/start-app.sh
```

That is `docker compose up --build -d`. Stop (volumes kept):

```bash
./docs/run/stop-app.sh
```

Reload catalogue seed (deletes, then inserts):

```bash
./docs/run/seed-db.sh
```

| Command | What it does |
| --- | --- |
| `./docs/run/start-app.sh` | Build and start in the background |
| `./docs/run/stop-app.sh` | Stop containers (volumes kept) |
| `./docs/run/seed-db.sh` | Delete and reload teaching + lifecycle seed |
| `docker compose -f docs/run/docker-compose.yml ps` | Process status |
| `docker compose -f docs/run/docker-compose.yml logs -f` | Follow all logs |
| `docker compose -f docs/run/docker-compose.yml logs -f agent-data-plane` | One service |
| `docker compose -f docs/run/docker-compose.yml logs -f otel-lgtm` | Grafana LGTM startup and collector |
| `docker compose -f docs/run/docker-compose.yml down -v` | Stop and **wipe** Postgres and LGTM data |

`start-app.sh` rebuilds images after code or **new** Flyway versions. Do not edit a migration that already ran: Flyway checksum-fails, Data Plane crash-loops, and Control Plane shows `Catalogue read failed (502)`. Recover with `docker compose -f docs/run/docker-compose.yml down -v`, then `./docs/run/start-app.sh`. To reload seed without a new migration, use `./docs/run/seed-db.sh`.

### Check it is up

```bash
curl -sf localhost:3005/health && echo
curl -sf localhost:3007/health && echo
curl -sf localhost:3008/health && echo
curl -sf localhost:3009/health && echo
```

Control Plane has no `/health`; open [http://localhost:3006](http://localhost:3006).

Grafana LGTM can take a minute. Wait until logs print `The OpenTelemetry collector and the Grafana LGTM stack are up and running.`, then open [http://localhost:3000](http://localhost:3000) (`admin` / `admin`).

## Ports and URLs

| Port | What | URL |
| --- | --- | --- |
| 3000 | Grafana (LGTM) | http://localhost:3000 |
| 3005 | Front Door (channel API) | http://localhost:3005 |
| 3006 | Control Plane (catalogue UI) | http://localhost:3006 |
| 3007 | Data Plane | http://localhost:3007 |
| 3008 | Agent Runtime | http://localhost:3008 |
| 3009 | Capability Registry | http://localhost:3009 |
| 4317 | OTLP gRPC ingestion | http://localhost:4317 |
| 4318 | OTLP HTTP ingestion | http://localhost:4318 |
| 5432 | Postgres 16 | `fabric` / `fabric` |
| 8080 | Adminer | http://localhost:8080 |

Adminer: System **PostgreSQL**, server **`postgres`**, user/password **`fabric`**. Databases: `afd`, `adp`, `ar`, `acr`. There is no Control Plane database.

Grafana: username **`admin`**, password **`admin`**. Dev/demo only — not a production observability stack.

## Observability (Grafana LGTM)

Compose includes [`grafana/otel-lgtm`](https://hub.docker.com/r/grafana/otel-lgtm): one container with OpenTelemetry Collector, Prometheus (metrics), Loki (logs), Tempo (traces), and Grafana. Collector receives OTLP and Grafana already has the data sources.

Run Grafana with the fabric, or only the backend:

```bash
docker compose -f docs/run/docker-compose.yml up otel-lgtm
```

### Send OpenTelemetry signals

From another Compose service, export to `otel-lgtm`:

| Transport | Endpoint |
| --- | --- |
| OTLP gRPC | `otel-lgtm:4317` |
| OTLP HTTP | `http://otel-lgtm:4318` |

From a process on the host (not in Compose), use `localhost:4317` or `http://localhost:4318`.

OpenTelemetry defaults to a 60s export interval. For local experiments, shorten it so data shows up faster:

```bash
export OTEL_METRIC_EXPORT_INTERVAL=500
```

Fabric services are not instrumented yet. Until they export OTLP, Grafana dashboards stay empty.

### Explore in Grafana

Log in at [http://localhost:3000](http://localhost:3000), then **Dashboards** (example HTTP/runtime dashboards) or **Explore** (pick a data source top-left).

**Metrics** (Prometheus / PromQL) — request rate:

```promql
rate(http_server_request_duration_seconds_count[$__rate_interval])
```

**Traces** (Tempo / TraceQL) — spans for a service, or HTTP 500s:

```traceql
{.service.name="agent-front-door"}
```

```traceql
{.service.name="agent-front-door" && .http.response.status_code=500}
```

**Logs** (Loki / LogQL):

```logql
{level="INFO"}
```

```logql
{level="INFO"} | json | line_format "{{.body}}"
```

### Persistence

LGTM writes to `/data` in the container. Compose mounts named volume `lgtm-data`, so metrics, logs, traces, and Grafana state survive `down`. Only `docker compose -f docs/run/docker-compose.yml down -v` deletes that volume (and Postgres).

## Components

```text
Chat / channel  →  Front Door :3005
                       │
                       ├─ decide / eligible / catalogue  →  Data Plane :3007
                       └─ start run                      →  Agent Runtime :3008
                                                              │
                                                              └─ hydrate tools → Registry :3009

Browser         →  Control Plane UI :3006  (reads Data Plane + Registry; does not decide)
Browser         →  Grafana :3000           (metrics, logs, traces via OTLP)
```

| Folder | Job | Stack | Database |
| --- | --- | --- | --- |
| [`agent-front-door`](agent-front-door/) | Channel ingress. Accepts the user turn, calls decide, starts the runtime. Chat JSON does not include `route_id` or `run_id`. | Java 21, Spring Boot, hexagonal | `afd` |
| [`agent-data-plane`](agent-data-plane/) | Routes, eligibility, keyword classify (`/v1/intent/*`), catalogue (`/v1/catalog/*`). Owns the route rows. Does **not** store decision audit. Only Front Door may call decide. | Java 21, Spring Boot, hexagonal | `adp` |
| [`agent-runtime`](agent-runtime/) | Executes the chosen route (hydrate tools, LangGraph loop). v1 stub node returns the canned fee sentence. | Python 3.12, FastAPI, uv, LangGraph | `ar` |
| [`agent-capability-registry`](agent-capability-registry/) | Published capabilities and manifests (`id@version`). Runtime hydrates from here at pin. | Java 21, Spring Boot, hexagonal | `acr` |
| [`agent-control-plane`](agent-control-plane/) | Catalogue browser only. Lists routes, capabilities, prompts, manifests. **No** decide API, **no** database. | TypeScript, Node 22 | none |

Supporting pieces:

| Path | Role |
| --- | --- |
| [`docs/run/`](docs/run/) | Compose file, start/stop/seed scripts, Postgres image, demo scripts |
| [`docs/contracts/`](docs/contracts/) | Frozen request/response fixtures and [stub auth](docs/contracts/stub-auth.md) |
| [`docs/`](docs/) | Architecture packs, [plan](docs/tasks/plan.md), and [future-enhancement.md](docs/future-enhancement.md) |

### Routes (v1)

Each route is versioned on its own (`route_id` + `route_version`). One version per route is `active`. Classify uses the active mix. A follow-up pin is that route’s id and version, not a shared table snapshot. A later contest-board snapshot is proposed in [docs/future-enhancement.md](docs/future-enhancement.md).

The catalogue seed is the Pattern 0–3 teaching set (29 routes, matching manifests, prompts, workflows, and Registry capabilities). IDs have no `v1`/`v3` suffix — version lives on `*_version` columns. `seed-db.sh` also loads extra published, draft, and retired cuts plus version history. Reload everything in one shot:

```bash
./docs/run/seed-db.sh
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
- [Future: versioned route table](docs/future-enhancement.md)
