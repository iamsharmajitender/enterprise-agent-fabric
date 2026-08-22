# Implementation Plan: Enterprise Agent Fabric v1 (local)

Observability (OTLP → LGTM, three layers) is a **separate** plan: [observability-plan.md](./observability-plan.md) / [observability-todo.md](./observability-todo.md). Do not fold those tasks into the checkboxes below.

## Overview

Stand up five independently deployable Fabric services in the existing folders, talking over the pack contracts, so `docker compose up` plus a scripted jobs call proves pin → hydrate → run, then a scripted chat turn proves entitle → classify → freeze → the same AR path. Chat `/v1/assistant/*` on Front Door comes **last**. Postgres is used by Front Door, Data Plane, Runtime, and Registry only. Control Plane has no database and **no APIs** — it only calls Data Plane. Kafka, IdP, and the LLM are stubbed. This plan implements the confirmed intent, not the full pack FR set.

**Confirmed intent:** [docs/intent/enterprise-agent-fabric-v1.md](../intent/enterprise-agent-fabric-v1.md)

**Confirmed intent (summary)**

- Outcome: five services in `agent-front-door`, `agent-control-plane`, `agent-data-plane`, `agent-runtime`, `agent-capability-registry`
- User: local platform you can run and grow
- Success: compose up; scripted jobs POST then GET; then scripted chat turn; slim chat response; four DBs written (`afd`, `adp`, `ar`, `acr`); Control Plane GETs routes/intent/catalogue from Data Plane; per-service contract tests. Chat `/v1/assistant/*` is the last feature phase.
- **Constraint:** Java hexagonal (Front Door, Registry, Data Plane); TypeScript Control Plane is a UI (no Fabric APIs, no DB) that calls Data Plane; Python AR with uv + LangGraph; HTTP on **3005, 3006 (CP UI), 3007, 3008, 3009**; stub Kafka / IdP / LLM; **no decision audit**; each service folder has a detailed `README.md`
- Out of scope: remaining case-study packs; real Kafka / IdP / LLM; two production AFD fleets; Patterns 0–3; dual-check; **decision audit**; real chat UI; production deploy / SLO maths

**Behaviour source:** [docs/enterprise-agent-fabric-architecture](../enterprise-agent-fabric-architecture/README.md). Do not reopen locked fabric rules. V1 implements them cheaply (HTTP instead of Kafka, stub identity, keyword Layer ②, LangGraph stub node).

## Architecture Decisions

- **Five processes, four databases, one Compose file.** `docs/run/compose/docker-compose.yml`. One Postgres 16 server, databases `afd`, `adp`, `ar`, `acr`. No `acp` database. HTTP: 3005 Front Door, **3006 Control Plane UI**, 3007 Data Plane, 3008 AR, 3009 Registry.
- **Frameworks.** Java 21 + Spring Boot 3 + Flyway on Front Door, Data Plane, Registry — **hexagonal** packages `domain`, `application`, `adapters.in` (REST), `adapters.out` (Postgres, HTTP). Domain has no Spring or SQL. Control Plane: TypeScript + Node 22 + `fetch`, **no HTTP server**, no `node-pg`. Runtime: Python 3.12, **uv**, FastAPI HTTP, SQLAlchemy 2 + Alembic, **LangGraph** for the run loop. No shared library in v1 — copy the contract fixtures, not a mono-runtime.
- **Hexagonal (Java three only).** Driving adapters: HTTP controllers. Driven adapters: Flyway/JDBC and sibling HTTP clients. Use cases live in `application`. Do not put decide/catalogue/freeze logic in controllers.
- **HTTP APIs between services.** Siblings call HTTP only — never another service’s Postgres, never a shared library. **Channel API:** Front Door `:3005` `/v1/jobs*` first (after AR), then `/v1/assistant/*` last. Same process; no second fleet. **Service APIs:** Data Plane `:3007` `/v1/intent/*` (eligible, decide) and `/v1/catalog/*` (route table + row, manifest pointers); AR `:3008` `/v1/runs*`; Registry `:3009` `/v1/capabilities*` and `/v1/manifests*`. **Control Plane** local UI on **3006** lists catalogue rows by calling Data Plane; it exposes no decide/audit APIs and has no database. Only AFD calls decide.
- **LangGraph, stub model.** After hydrate, AR runs a LangGraph graph. v1’s only node emits the canned fee message. No live LLM, no domain HTTP invoke. `uv add` / `uv run` / `uv lock` — not pip or Poetry.
- **Stub IdP.** Channel calls send `Authorization: Bearer stub` and `X-Stub-Claims` (JSON). Workload calls send `Authorization: Bearer fabric-internal` and `X-Workload` (`afd` | `adp` | `acp` | `ar` | `acr`). Reject anything else. Map stub user `jane` to claim `accounts:read`.
- **Stub Kafka.** No `{runs_topic}`. AFD polls AR `GET /v1/runs/{correlation_id}`. Chat uses HTTP poll on `/v1/assistant/sessions/{id}/events`, not SSE. **Decision audit is out of scope** — not on Data Plane, not on Control Plane.
- **Stub LLM.** Layer ② is keyword retrieve over eligible routes (no Layer ③). AR hydrates for real, then LangGraph’s stub node writes the canned `completed` result.
- **Per-service handbook.** Each of the five folders has a detailed `README.md` (not a stub). Same headings in every file: job, port/stack, auth, APIs, contracts, schema/tables (or none), sibling calls, non-goals, how to run tests. Root README only points at compose + these five files.
- **Demo route.** Seed `fee_explain` @ `route_table_version=2026.08.1`, chat-visible, channel `web`, required claim `accounts:read`. Utterance `"Why was I charged $42?"` → `outcome=route`. AR result: `"Fee of $42 is the monthly account charge."`
- **One AFD process.** Port 3005. Jobs `/v1/jobs*` lands after AR (Phase 6). Chat `/v1/assistant/*` is the same codebase and deployment, last (Phase 7). A second production fleet (separate hostname/HPA) stays out of scope.
- **ACP vs Data Plane stay split.** Data Plane owns routes, intent (eligible/decide), and catalogue rows (including manifest pointers). Control Plane is a **client** of those read APIs. Data Plane does not pin, start AR, or keep an audit log. Control Plane is not on the decide hot path.

## Demo path (definition of done for the plan)

Jobs first (after AR):

```text
POST :3005/v1/jobs   { route_id: "fee_explain", idempotency_key, payload }
GET  :3005/v1/jobs/{correlation_id}   until status completed
```

Jobs POST names `route_id`; `202` may return `correlation_id`.

Chat last:

```text
GET  :3005/v1/assistant/hints
POST :3005/v1/assistant/turns   { message: "Why was I charged $42?" }
GET  :3005/v1/assistant/sessions/{id}/events   until status completed
```

Then prove rows exist in afd (freeze), adp (catalogue used to decide),
ar (run pin + hydrated_tools), acr (published capability/manifest read at hydrate).
Prove Control Plane called Data Plane GET eligible and GET catalogue/route (not an audit API).

Chat JSON never contains `route_id`, `run_id`, `agent_client_id`, `confidence`, or `router_layer` (FR-5).

## Task List

### Phase 1: Local fabric boots

- [x] Task 1: Compose Postgres (four databases) and stub-auth contract
- [x] Task 2: Pack JSON fixtures under `docs/contracts/`
- [x] Task 3: Registry hexagonal Spring Boot health on 3009
- [x] Task 4: Data Plane hexagonal Spring Boot health on 3007
- [x] Task 5: Control Plane worker (no HTTP, no port)
- [x] Task 6: Runtime uv + FastAPI health on 3008
- [x] Task 7: Front Door hexagonal Spring Boot health on 3005

### Checkpoint: Foundation

- [x] `docker compose -f docs/run/compose/docker-compose.yml up` — `/health` 200 on 3005, 3007, 3008, 3009; Control Plane process running with no published port; Adminer on 8080
- [x] Four empty databases exist (`afd`, `adp`, `ar`, `acr`); Control Plane has none
- [ ] Review with human before contract work

### Phase 2: Registry persist (hydrate needs this)

- [x] Task 8: Capability `PUT`/`GET` by `id@version`
- [x] Task 9: Manifest `PUT`/`GET` at named version
- [x] Task 10: Registry contract tests (409 on published overwrite)

### Checkpoint: Registry

- [x] Publish `account_fee_lookup@1.0.0` and manifest `fee_explain_v1@2026.08.1`; GET both

### Phase 3: Catalogue and decide

- [x] Task 11: Catalogue schema + seed `fee_explain`
- [x] Task 12: `GET` eligible + `GET` catalogue row at pinned version
- [x] Task 13: `POST /v1/intent/decide` (entitle + Layer ① bind + Layer ② keywords)

### Checkpoint: Decide

- [x] `$42` utterance → `outcome=route`, `route_id=fee_explain`
- [x] Missing claims → `abstain`. Ambiguous message → `clarify` with opaque-ready candidates

### Phase 4: Control Plane as Data Plane client

- [x] Task 14: Control Plane GETs eligible + catalogue/route from Data Plane
- [x] Task 15: Data Plane has no audit/decisions API or table

### Checkpoint: Control Plane client

- [x] Control Plane `fetch` of eligible and `fee_explain` catalogue row succeeds
- [x] `GET /v1/decisions` does not exist on Data Plane; decide still 200 with Control Plane stopped

### Phase 5: Runtime pin, hydrate, LangGraph stub loop

- [x] Task 16: `POST /v1/runs` → `202` + idempotency
- [x] Task 17: Hydrate from Data Plane row + Registry before `202`
- [x] Task 18: LangGraph stub complete + `GET` status + open-run by `session_id`

### Checkpoint: AR

- [x] Start with seed pin → `202`; `GET` returns canned message; duplicate `idempotency_key` does not mint a second run
- [x] Missing published ref → no `202`

### Phase 6: Jobs on the same Front Door

- [x] Task 30: `POST /v1/jobs` + `GET /v1/jobs/{id}` on the same process (Layer ①, no second fleet)
- [x] Task 31: Jobs demo + Front Door jobs handbook

### Checkpoint: Jobs path

- [x] `POST /v1/jobs` for `fee_explain` → `202`; GET completes with canned message
- [x] Still one `agent-front-door` Compose service
- [ ] Review before chat path

### Phase 7: Front Door chat path (last)

- [ ] Task 19: Freeze table + session mint
- [ ] Task 20: Hints + turn (decide → freeze → start) with FR-5 slim JSON
- [ ] Task 21: Poll events until AR completed
- [ ] Task 22: Continuation skips decide

### Checkpoint: Chat path

- [ ] One turn from hints through completed slim message
- [ ] Continuation does not call decide (AFD test; Data Plane decide is not invoked)

### Phase 8: Scripted chat demo

- [x] Task 23: `docs/run/scripts/demo-chat-turn.sh` + seed + four-DB assertions + Control Plane catalogue fetch

### Phase 9: Service handbooks

- [ ] Task 25: `agent-capability-registry/README.md`
- [ ] Task 26: `agent-data-plane/README.md`
- [ ] Task 27: `agent-control-plane/README.md`
- [ ] Task 28: `agent-runtime/README.md`
- [ ] Task 29: `agent-front-door/README.md` (chat APIs; jobs already in Task 31)
- [ ] Task 24: Root README (compose, ports, jobs + chat demos, links to service handbooks)

### Checkpoint: Complete

- [ ] All acceptance criteria in `docs/tasks/todo.md` through Task 24 met
- [ ] Definition of Done (correctness + tests) for each service
- [ ] All five service `README.md` files match the running jobs and chat APIs and schemas

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Three Java copies drift | Med | Same hexagonal Spring/Flyway layout; contract fixtures in `docs/contracts/` are the shared source |
| “Complete services” expands into pack FRs | High | Out of scope stays in this plan; second AFD fleet / SSE / Kafka / Layer ③ are later plans |
| LangGraph pulls in a live model | Med | Graph has a stub node only; no API key in compose |
| Hexagonal collapses into controllers | Med | Domain tests with fakes; no Spring imports under `domain/` |
| Decision audit sneaks onto Data Plane | High | Data Plane APIs are eligible, decide, catalogue only; Task 15 forbids `/v1/decisions` |
| Service README drifts from code | Med | Tasks 25–29 run after that service’s APIs exist; verify paths/tables against code |

## Open Questions

None that block v1. Framework defaults above are locked: hexagonal Spring for the three Java services, TypeScript `fetch` client for Control Plane (no Fastify), uv + LangGraph for AR.
