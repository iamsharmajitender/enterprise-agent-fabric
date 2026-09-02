# Intent: Enterprise Agent Fabric v1 (local)

**Status:** Confirmed 2026-08-20 (AR, HTTP APIs, Control Plane is a Data Plane client, no audit on Data Plane)  
**Plan:** [tasks/plan.md](../tasks/plan.md) · [tasks/todo.md](../tasks/todo.md)  
**Docs map:** [README.md](../README.md)  
**Behaviour source:** [04-architecture](../04-architecture/index.mdx)

Do not reopen locked fabric rules. This file is what to build, not how the packs work.

## Confirmed intent

- **Outcome:** Five independently deployable Fabric services in the folders already made — Front Door, Control Plane, Data Plane, Runtime, Capability Registry — talking over the pack contracts.
- **User:** You, running and growing this platform locally.
- **Why now:** The solution packs exist; the five folders were empty; running software is next.
- **Success:** `docker compose up`, then one scripted chat turn: message in, slim response out, entitle → classify → pin → hydrate → run. Four Postgres databases written (Front Door, Data Plane, Runtime, Registry). Control Plane proves it ran by calling Data Plane for **routes / intent / catalogue (manifest pointers)**. Each service has tests for its own contract. Each service folder has a detailed `README.md`. Jobs `/v1/jobs*` on the **same** Front Door process is next after that chat complete checkpoint.
- **Constraint:** Java hexagonal architecture (Front Door, Registry, Data Plane). TypeScript Control Plane is a **UI only** (no database, no Fabric service APIs). It talks to Data Plane over HTTP. Python **Agent Runtime (AR)** with **uv** and **LangGraph**. Postgres on Front Door, Data Plane, AR, and Registry. HTTP: **3005, 3006 (CP UI), 3007, 3008, 3009**. Stub Kafka, IdP, and the LLM.
- **Out of scope:** Remaining case-study packs. Real Kafka / IdP / LLM. Full pack FRs (two production AFD fleets, Patterns 0–3, dual-check). **Decision audit** (no audit store, no `/v1/decisions`). A real chat UI. Production deploy and SLO maths.

## Locked for v1 (so the plan does not drift)

- One Compose file at `agent-fabric-scripts/docker-compose/docker-compose.yml`. One Postgres 16 server; databases `afd`, `adp`, `ar`, `acr` only. No `acp` database.
- The box is **AR** (Agent Runtime), not NAR. Workload header `X-Workload: ar`. Database `ar`.
- Services talk only via HTTP. No service reads another service’s Postgres. Channel callers use Front Door only.
- **Control Plane has no Fabric service APIs** (no decide, no audit) and no database. It calls Data Plane with `X-Workload: acp`. Local **catalogue UI** on **3006** lists route rows and shows playbook field detail.
- **Data Plane is routes, intent, and catalogue only** (eligible, decide, catalogue row including manifest **pointers**). It does **not** store or serve decision audit. No `/v1/decisions`. No audit table in `adp`.
- Front Door, Data Plane, and Registry: Java 21 + Spring Boot 3 + Flyway, **hexagonal**. Domain has no Spring or SQL.
- Control Plane: TypeScript + Node 22 + `fetch`. Native HTTP **catalogue UI** on 3006 (no Fastify, no `node-pg`). Calls Data Plane `GET /v1/catalog/routes` and `GET /v1/catalog/routes/{route_id}` (and eligible). Does **not** call decide.
- Runtime: Python 3.12, **uv**, FastAPI, **LangGraph** stub node (canned fee message).
- Chat `/v1/assistant/*` first on one Front Door process (port 3005). Jobs `/v1/jobs*` on that same process **after** the chat complete checkpoint. A second production AFD fleet is later.
- Layer ② is keyword retrieve. AR hydrates for real, then LangGraph completes with the canned result.
- Demo: `"Why was I charged $42?"` → `fee_explain` @ `2026.08.1` → `"Fee of $42 is the monthly account charge."`
- Chat JSON never contains `route_id`, `run_id`, `agent_client_id`, `confidence`, or `router_layer`.
- Each service folder has a detailed `README.md`. Control Plane README states **no APIs**; Data Plane README does **not** mention audit.

## Next

Implement from Task 1 in `agent-fabric-docs/tasks/todo.md` (`/build`). Do not start a new design.
