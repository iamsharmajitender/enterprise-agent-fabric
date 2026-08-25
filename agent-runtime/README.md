# Agent Runtime

Executes a **pinned** route after Front Door has already decided. Does **not** classify utterances, own agent identity, or store conversation / long-term memory.

Request order in the fabric: **AFD → ADP (decide / pin pointers) → AR (this service) → ACR (hydrate)**. Only AFD may call Runtime (`X-Workload: afd`).

Local stack: Compose service `agent-runtime`, typically `:3008`.

## Layout

```text
app/
  api/                 # FastAPI: auth middleware, /health, /v1/runs*
  agents/
    hydrate.py         # Resolve route → hydrated tool/stage list
    clients.py         # HTTP clients for ADP catalogue + ACR
  core/
    agent_core.py      # RunService: start / resume / status / open-run
    execution.py       # graph.invoke → complete or fail the pin
    run_store.py       # Postgres pins (idempotency, status, working, checkpoint)
    memory.py          # When to flush working notes / loop checkpoint
    state.py           # RunPin model + store protocol
  graph/
    workflow.py        # LangGraph builders (linear stages + Pattern 1 loop)
    llm/               # LlmPort, SeedStubLlm, ProviderLlm, llm_from_env
  tools/
    invoker.py         # HTTP POST/GET to capability invoke.url
  telemetry.py         # OTel spans + business events
```

## End-to-end: one run

```text
POST /v1/runs  (from AFD)
  → workload auth
  → RunService.start
       1. idempotency_key hit? return existing correlation_id
       2. hydrate (catalogue + registry) → list of pinned capabilities/stages
       3. insert RunPin (status=running)
       4. build graph from autonomy_mode + hydrated tools
       5. run_loop → graph.invoke({ goal, notes })
       6. store.complete({ message }) or mark failed
  → 202 { correlation_id }
```

Follow-ups: `POST /v1/runs/{correlation_id}/turns` reloads the pin, rebuilds the graph from **already hydrated** tools, optionally restores `working.notes`, invokes again.

Status: `GET /v1/runs/{correlation_id}`. Latest by session: `GET /v1/runs?session_id=…`.

### What is **not** here

| Topic | Reality today |
| --- | --- |
| **HTTP retries** on tool calls | None — `HttpToolClient` raises on non-2xx |
| **Graph retries** / resume-from-failed-step | None — exception → run `failed`; resume is a new invoke with prior notes if configured |
| **Child `kind=agent` jobs** | Skipped with a note (`agent skipped…`) |
| **Classify / decide** | ADP before AR |

Idempotency on **start** (`idempotency_key`) is the main “don’t double-start” guard, not a retry loop.

## Hydrate

`app/agents/hydrate.py` turns the pinned `route_id` + `route_version` into an ordered list the graph can run.

1. Load route row from ADP (`CataloguePort.get_route`).
2. **If** `tool_manifest` + version are set → ACR `get_manifest` → each `get_capability` (schemas + `invoke.url` frozen on the pin).
3. Stamp `llm_role` / `llm_prompt` from the route’s workflow + prompt pack when present.
4. **Else** no manifest → build nodes from **workflow stages** (invoke empty) or **prompt-only** (Pattern 0 single synthesis node).
5. Pattern 2/3 HTTP-only lists get a trailing `respond` synthesis node if no classify/synthesis stage exists (`_ensure_llm`).

Hydrate failure → `422 HYDRATE_FAILED` (no `202`). Successful hydrate is frozen on `RunPin.hydrated_tools` for the life of the run (resume does not re-hydrate).

## Graphs (agent “framework”)

Today the executor is **LangGraph**, wrapped behind `GraphPort.invoke(state)`.

| Autonomy | Builder | Behavior |
| --- | --- | --- |
| `0` / `2` / `3` (and default) | `build_tool_graph` | Linear nodes in hydrate order |
| `1` | `build_agent_loop` | LLM emits `CALL <tool_id>` / `DONE <answer>` up to `max_loop_steps` |

Each linear stage (`_run_stage`) uses `llm_role`:

| `llm_role` | Behavior |
| --- | --- |
| `none` | HTTP to `invoke.url` with `dict(goal)` (+ query if formulated) |
| `query_formulation` | LLM writes `payload["query"]`, then HTTP |
| `classify` / `synthesis` | LLM only; append text to `notes`; no HTTP |
| empty `invoke.url` | No-op / carry prior result (prefetch placeholders) |

`GraphState`: `{ result, goal, notes }`. The user-facing reply is `result` → stored as `{ "message": "…" }`.

### Changing the agent framework

Callers depend on `GraphPort` (`invoke(state) → state`), not LangGraph types.

1. Implement another builder that returns an object with `.invoke(dict)`.
2. Either inject it into `RunService(graph=…)` / `create_app(graph=…)`, or replace the `build_tool_graph` / `build_agent_loop` calls in `agent_core._graph_for`.
3. Keep hydrate’s list shape (`id`, `invoke`, `llm_role`, `llm_prompt`, …) stable so tools and LLM ports stay unchanged.

LangGraph lives only in `app/graph/workflow.py`.

## Tools

`HttpToolClient` (`app/tools/invoker.py`):

- Reads `invoke.method` + `invoke.url` from the **hydrated** capability.
- Sends JSON body (usually `dict(goal)`, maybe with `query`).
- Forwards `X-Request-Id`.
- Span: `tool.invoke`.
- Local Compose URLs point at `http://tool-mock:3010…` ([`agent-fabric-mocks/tools`](../agent-fabric-mocks/tools/)).

Swap invokers by implementing `ToolInvoker.call(invoke, payload)` and passing `tool_invoker=` into `create_app` / `RunService`.

## LLM

Port: `LlmPort.complete(system, user) → str` (`app/graph/llm/`).

| Piece | Role |
| --- | --- |
| `factory.llm_from_env` | `FABRIC_LLM_STUB=1` → stub; else `ProviderLlm` |
| `SeedStubLlm` | Deterministic CALL/DONE + canned lines (Compose default) |
| `ProviderLlm` | Real completer; **today** LangChain + Ollama inside `_build_default_backend` |
| `plain_text` | Normalize model content / strip think-tags |

### Changing the LLM / SDK

1. Keep using `LlmPort`.
2. Replace `_build_default_backend()` in `app/graph/llm/provider.py` (or inject a backend into `ProviderLlm(backend=…)`).
3. Wire via `create_app(llm=…)` or env (`FABRIC_LLM_STUB`, `OLLAMA_*`, optional `FABRIC_LLM_MODEL`).

Do **not** import LangChain from `workflow.py` / `agent_core.py` — only through `LlmPort`.

## Memory (working + checkpoint)

From the catalogue `memory_profile` on the route (`app/core/memory.py`):

| Flag | Effect |
| --- | --- |
| `working=session` | After each stage, flush `notes` to `runtime.runs.working`; resume reloads them |
| `loop=checkpoint` | After each stage, write `{ step, stage_id, result, goal }` to `checkpoint` |

Crash resume-from-step is **not** wired; checkpoint is persistence for observability / future resume.

## Auth and identity

- Ingress: `Authorization: Bearer fabric-internal` + `X-Workload: afd` (only AFD).
- Outbound to ADP/ACR: workload headers from HTTP clients.
- Channel user claims are **not** re-checked here; AFD already entitled the start.

## Key environment

| Variable | Purpose |
| --- | --- |
| `DATA_PLANE_URL` | Catalogue HTTP (routes, workflows, prompts) |
| `REGISTRY_URL` | ACR hydrate |
| `DATABASE_URL` / store config | Run pins |
| `FABRIC_LLM_STUB` | `0` = provider (Compose default); `1` = stub |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Default provider backend |
| `FABRIC_LLM_MODEL` | Optional model id override for provider |
| `OTEL_*` | Tracing / metrics |

## Tests

```bash
cd agent-runtime
pytest
```

Notable suites: hydrate, graph stages, LLM stub/provider, runs + idempotency, memory flush, telemetry.

Inject fakes via `create_app(store=…, catalogue=…, registry=…, graph=…, tool_invoker=…, llm=…)`.

## Related docs

- Fabric overview: [`../README.md`](../README.md)
- Patterns 0–3: [`../docs/06-patterns/`](../docs/06-patterns/)
- Stub auth: [`../docs/05-reference/stub-auth.md`](../docs/05-reference/stub-auth.md)
- Domain tool doubles: [`../agent-fabric-mocks/tools/`](../agent-fabric-mocks/tools/)
