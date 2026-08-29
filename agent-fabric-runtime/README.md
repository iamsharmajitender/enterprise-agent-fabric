# Agent Runtime

Executes a **pinned** route after Front Door has already decided. Does **not** classify utterances, own agent identity, or store conversation / long-term memory.

## Job

Copy the freeze into a durable run pin, hydrate tools from ADP + ACR, run LangGraph (Patterns 0–3), invoke domain HTTP (local: agent-fabric-mocks), honor `working` / `loop` on the pin. Only AFD may start this box (`X-Workload: afd`).

## Port / stack

| | |
| --- | --- |
| Port | **3008** |
| Stack | Python 3.12, **uv**, FastAPI, SQLAlchemy 2 + Alembic, **LangGraph** |
| Database | `ar` (schema `runtime`) |
| Compose | `agent-runtime` |
| Auth | Ingress: workload `afd` only |

Request order: **AFD → ADP (decide / pin pointers) → AR (this service) → ACR (hydrate)**.

Docs map: [docs/README.md](../agent-fabric-docs/README.md). Box pack: [docs/04-architecture/agent-runtime.md](../agent-fabric-docs/04-architecture/agent-runtime.md). Stub auth: [05-reference/stub-auth.md](../agent-fabric-docs/05-reference/stub-auth.md).

## Hexagonal layout

Python layout (ports via protocols / injected clients):

```text
app/
  api/                 # FastAPI: auth middleware, /health, /v1/runs*
  agents/
    hydrate.py         # Resolve route → hydrated tool/stage list
    clients.py         # HTTP clients for ADP catalogue + ACR
    jobs_client.py     # kind=agent → AFD /v1/jobs
    prefetch.py        # deterministic_prefetch pack
  core/
    agent_core.py      # RunService: start / resume / status / open-run
    execution.py       # graph.invoke → complete, waiting, or fail
    run_store.py       # Postgres pins
    memory.py          # working notes/slots + loop checkpoint
    checkpoint.py      # resume_index helpers
    state.py           # RunPin model + store protocol
  graph/
    workflow.py        # LangGraph builders (linear, branch, gate, Pattern 1)
    llm/               # LlmPort, SeedStubLlm, ProviderLlm, llm_from_env
  tools/
    invoker.py         # HTTP to capability invoke.url
  telemetry.py         # OTel spans + business events
```

## Auth

Ingress:

```http
Authorization: Bearer fabric-internal
X-Workload: afd
```

Outbound to ADP/ACR: workload headers from HTTP clients. Channel user claims are **not** re-checked here; AFD already entitled the start.

## APIs

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"UP"}` |
| `POST` | `/v1/runs` | `mode: new`. Hydrate + pin **before** `202`. Graph runs in the background. Idempotent on `idempotency_key`. Body includes `session_id`, `route_id`, `route_version`, `goal`. |
| `GET` | `/v1/runs/{correlation_id}` | Slim status |
| `GET` | `/v1/runs?session_id=` | Open-run (latest for session) |
| `POST` | `/v1/runs/{correlation_id}/turns` | Resume: reload working; human_gate packet; checkpoint resume (`{}` / `{ "resume": true }`) |

Hydrate failure → **422** `HYDRATE_FAILED` (no `202`). Successful hydrate freezes `hydrated_tools` on the pin for the life of the run. Clients observe completion via `GET /v1/runs/{correlation_id}` (AFD: `GET /v1/jobs/{correlation_id}`).

### End-to-end: one run

```text
POST /v1/runs  (from AFD)
  → RunService.start
       1. idempotency_key hit? return existing correlation_id
       2. hydrate (catalogue + registry) → list of pinned capabilities/stages
       3. insert RunPin (status=running)
       4. return 202 { correlation_id }
       5. (background) build graph + run_loop → complete / pause / fail
```

## Contracts

- [`agent-fabric-docs/05-reference/run-start.json`](../agent-fabric-docs/05-reference/run-start.json)
- [`agent-fabric-docs/05-reference/run-status-completed.json`](../agent-fabric-docs/05-reference/run-status-completed.json)
- [`agent-fabric-docs/05-reference/stub-auth.md`](../agent-fabric-docs/05-reference/stub-auth.md)

## Tables / schema

Alembic / Flyway-style `V1__runtime.sql` on `ar`:

| Column | Role |
| --- | --- |
| `correlation_id` | PK (`corr-*`) |
| `idempotency_key` | Unique start key |
| `session_id` | Chat `chat-{uuid}` or jobs `job-{uuid}` / subagent `sub-{uuid}` |
| `route_id` / `route_version` | Pinned catalogue cut |
| `hydrated_tools` | Frozen capability list JSON |
| `status` | `running` / `waiting` / `completed` / `failed` |
| `result` | Slim result JSON (`message`, …) |
| `working` | `{ "notes": [...], "slots": { … } }` when `working=session` |
| `checkpoint` | `{ step, stage_id, result, goal, resume_index, … }` when `loop=checkpoint` |

Index: `(session_id, status)` for open-run.

## Sibling calls

| Direction | Call | Notes |
| --- | --- | --- |
| In | AFD `POST /v1/runs`, `/turns`, status, open-run | Only `afd` |
| Out | ADP catalogue GET | Route, workflow, prompt, corpora |
| Out | ACR GET | Manifest + each capability at pin |
| Out | agent-fabric-mocks / domain `invoke.url` | Stage HTTP |
| Out | AFD `POST /v1/jobs` | `kind=agent` child start (projected payload) |

## Non-goals

- Classify / decide (ADP)
- Shared Memory `conversation` / `long_term` ([future-enhancement](../agent-fabric-docs/tasks/future-enhancement.md#shared-memory-conversation-and-long_term))
- HTTP retries on tool calls
- Mid-loop registry GET (hydrate once)

### What is **not** here (detail)

| Topic | Reality today |
| --- | --- |
| **HTTP retries** on tool calls | None — non-2xx raises |
| **Graph resume** | `loop=checkpoint` failed runs resume from `resume_index` via `/turns` |
| **Child `kind=agent`** | POST AFD `/v1/jobs` with projected `payload` only |
| **LLM** | Env-selected: stub (`FABRIC_LLM_STUB=1`) or provider (Compose often Ollama). Not “never a model.” |

## Tests

```bash
cd agent-runtime && uv run pytest
```

Notable suites: hydrate, graph (slots / branch / gate), prefetch, checkpoint, runs + idempotency, memory, LLM schema, jobs client.

Inject fakes via `create_app(store=…, catalogue=…, registry=…, graph=…, tool_invoker=…, llm=…)`.

---

## Hydrate

`app/agents/hydrate.py` turns the pinned `route_id` + `route_version` into an ordered list the graph can run.

1. Load route row from ADP (`CataloguePort.get_route`).
2. **If** `tool_manifest` + version are set → ACR `get_manifest` → each `get_capability` (schemas + `invoke.url` frozen on the pin).
3. Stamp `llm_role` / `llm_prompt` from the route’s workflow + prompt pack when present.
4. **Else** no manifest → workflow stages or prompt-only Pattern 0.
5. Pattern 2/3 HTTP-only lists get a trailing `respond` synthesis node if needed (`_ensure_llm`).

## Graphs

| Autonomy | Builder | Behavior |
| --- | --- | --- |
| `0` / `2` / `3` | `build_tool_graph` | Linear or branch; `human_gate` → `waiting` |
| `1` | `build_agent_loop` | `CALL` / `DONE` up to `max_loop_steps` |

HTTP payload = `goal` ∪ schema-selected **slots** ([payload.py](app/graph/payload.py)). LLM reads `notes`. Prefetch writes `working.slots.prefetch`.

## Memory (working + checkpoint)

| Flag | Effect |
| --- | --- |
| `working=session` | Flush `{ notes, slots }` after each stage; `/turns` reloads both |
| `loop=checkpoint` | Write checkpoint + `resume_index`; failed runs resume via `/turns` |

## Key environment

| Variable | Purpose |
| --- | --- |
| `DATA_PLANE_URL` | Catalogue HTTP |
| `REGISTRY_URL` | ACR hydrate |
| `AFD_URL` | Child jobs (`kind=agent`) |
| `DATABASE_URL` | Run pins |
| `FABRIC_LLM_STUB` | `1` = stub; `0` = provider |
| `OLLAMA_*` / `FABRIC_LLM_MODEL` | Provider backend |
| `OTEL_*` | Tracing / metrics |

## Related docs

- **Runtime options (deploy, transforms, observability):** [agent-fabric-runtime-options.md](./agent-fabric-runtime-options.md)
- **Technical implementation (end-to-end):** [technical-implementation.md](./technical-implementation.md)
- Fabric overview: [`../README.md`](../README.md)
- Patterns 0–3: [`../agent-fabric-docs/06-patterns/`](../agent-fabric-docs/06-patterns/)
- Dataflow: [`../agent-fabric-docs/tasks/dataflow-plan.md`](../agent-fabric-docs/tasks/dataflow-plan.md)
- Domain tool doubles: [`../agent-fabric-mocks/tools/`](../agent-fabric-mocks/tools/)
