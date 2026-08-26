# Task list: Enterprise Agent Fabric v1 (local)

Plan: [plan.md](./plan.md). Docs map: [docs/README.md](../README.md).

Ports: **3005** Front Door · **3006** Control Plane UI · **3007** Data Plane · **3008** AR · **3009** Registry. Control Plane: no database.

**Remaining execution order** (task numbers stay): handbooks 25–29 + root README 24 are **done**. Final checkpoint below.

**Observability** (O1–O16): [observability-todo.md](./observability-todo.md) — signed off.

**Evals** (E1–E14): [eval-todo.md](./eval-todo.md) — done.

**Intent router** (I1–I11, I13–I14): [intent-todo.md](./intent-todo.md) — I12 deferred to [future-enhancement.md](./future-enhancement.md#i12-layer-3-llm-fallback).

**Stage data sharing** (D1–D13): [dataflow-todo.md](./dataflow-todo.md) — signed off.

---

## Task 1: Compose Postgres and stub-auth contract

**Description:** Compose in `docs/run/` starts Postgres 16 with databases `afd`, `adp`, `ar`, `acr` (no `acp`), plus Adminer for browsing those databases. Document the stub IdP headers every service will enforce.

**Acceptance criteria:**
- [x] `docker compose -f docs/run/compose/docker-compose.yml up postgres` creates those four databases and no `acp`
- [x] Adminer is in the same Compose file on host port 8080 (System PostgreSQL, server `postgres`, user/password `fabric`)
- [x] `docs/05-reference/stub-auth.md` defines channel `Bearer stub` + `X-Stub-Claims` and workload `Bearer fabric-internal` + `X-Workload`
- [x] `docs/run/compose/.env.example` lists DB URLs for the four services, HTTP ports 3005 / 3007 / 3008 / 3009, and Adminer 8080

**Verification:**
- [x] `docker compose -f docs/run/compose/docker-compose.yml exec postgres psql -U fabric -d afd -c '\l'` shows `afd`, `adp`, `ar`, `acr` only (plus Postgres templates; no `acp`)
- [x] `curl -sf -o /dev/null localhost:8080` — Adminer login page
- [x] Manual check: no service code required yet

**Dependencies:** None

**Files likely touched:**
- `docs/run/compose/docker-compose.yml`
- `docs/run/compose/init-postgres.sql`
- `docs/run/compose/.env.example`
- `docs/05-reference/stub-auth.md`

**Estimated scope:** Small

---

## Task 2: Pack JSON fixtures under `docs/contracts/`

**Description:** Freeze the request/response bodies from the architecture packs as JSON files the services must accept/emit. Demo utterance and canned AR result live here.

**Acceptance criteria:**
- [x] Fixtures exist for decide (chat route / clarify / abstain), AFD turn, AR start, AR status, capability, manifest
- [x] Demo message is `"Why was I charged $42?"`; canned result is `"Fee of $42 is the monthly account charge."`
- [x] Chat-slim fixtures contain none of `route_id`, `run_id`, `agent_client_id`, `confidence`, `router_layer`

**Verification:**
- [x] Manual check: files match pack examples in `docs/04-architecture/`

**Dependencies:** None

**Files likely touched:**
- `docs/05-reference/decide-chat-route.json`
- `docs/05-reference/assistant-turn-request.json`
- `docs/05-reference/run-start.json`
- `docs/05-reference/capability-account-fee-lookup.json`
- `docs/05-reference/manifest-fee-explain.json`

**Estimated scope:** Small

---

## Task 3: Registry hexagonal Spring Boot health on 3009

**Description:** `agent-capability-registry` boots as Java 21 / Spring Boot 3, Flyway against `acr`, hexagonal layout, Dockerfile, Compose on 3009. This is the Java template the other two copy.

**Acceptance criteria:**
- [x] `GET /health` returns 200 from an inbound adapter; health use case lives outside the controller
- [x] Packages exist: `domain`, `application`, `adapters.in`, `adapters.out`; no Spring or SQL imports under `domain/`
- [x] App uses database `acr` only; Compose on host port 3009

**Verification:**
- [x] `docker compose -f docs/run/compose/docker-compose.yml up agent-capability-registry` then `curl -sf localhost:3009/health` → `{"status":"UP"}`
- [x] Tests pass in the image build (`mvn test`; no local JDK)

**Dependencies:** Task 1

**Files likely touched:**
- `agent-capability-registry/pom.xml` or `build.gradle.kts`
- `agent-capability-registry/src/main/java/**/domain/**`
- `agent-capability-registry/src/main/java/**/adapters/in/**`
- `agent-capability-registry/Dockerfile`
- `docs/run/compose/docker-compose.yml`

**Estimated scope:** Medium

---

## Task 4: Data Plane hexagonal Spring Boot health on 3007

**Description:** Same hexagonal Java pattern as Registry for `agent-data-plane`, database `adp`, port 3007.

**Acceptance criteria:**
- [x] `GET /health` returns 200 from an inbound adapter
- [x] Packages: `domain`, `application`, `adapters.in`, `adapters.out`; no Spring or SQL under `domain/`
- [x] App uses database `adp` only; Compose on host port 3007

**Verification:**
- [x] `curl -sf localhost:3007/health`

**Dependencies:** Task 1, Task 3 (copy hexagonal Java layout)

**Files likely touched:**
- `agent-data-plane/**`
- `docs/run/compose/docker-compose.yml`

**Estimated scope:** Medium

---

## Task 5: Control Plane worker (no HTTP, no port)

**Description:** `agent-control-plane` is TypeScript / Node 22. It is a **client**: no listen port, no Fastify, no database. Compose runs it without publishing 3006.

**Acceptance criteria:**
- [x] Process starts in Compose with no published ports
- [x] App has no Postgres URL, no `node-pg`, no HTTP server
- [x] `X-Workload: acp` is the only identity it uses on outbound calls

**Verification:**
- [x] `npm test` in `agent-control-plane` (boot smoke)
- [x] `docker compose ps` shows the service running; `curl localhost:3006` fails

**Dependencies:** Task 1

**Files likely touched:**
- `agent-control-plane/package.json`
- `agent-control-plane/src/main.ts`
- `agent-control-plane/Dockerfile`
- `docs/run/compose/docker-compose.yml`

**Estimated scope:** Medium

---

## Task 6: Runtime uv + FastAPI health on 3008

**Description:** `agent-runtime` is Python 3.12 managed with **uv**, FastAPI HTTP, Alembic against `ar`, LangGraph on the classpath even if the graph is wired in Task 18. Port 3008.

**Acceptance criteria:**
- [x] `GET /health` returns 200
- [x] `uv.lock` exists; `uv run pytest` is the test command; Dockerfile uses `uv`
- [x] App uses database `ar` only; Compose on host port 3008

**Verification:**
- [x] `uv run pytest` in `agent-runtime` (health smoke)
- [x] `curl -sf localhost:3008/health`

**Dependencies:** Task 1

**Files likely touched:**
- `agent-runtime/pyproject.toml`
- `agent-runtime/uv.lock`
- `agent-runtime/app/main.py`
- `agent-runtime/Dockerfile`
- `docs/run/compose/docker-compose.yml`

**Estimated scope:** Medium

---

## Task 7: Front Door hexagonal Spring Boot health on 3005

**Description:** Same hexagonal Java pattern as Registry for `agent-front-door`, database `afd`, port 3005.

**Acceptance criteria:**
- [x] `GET /health` returns 200 from an inbound adapter
- [x] Packages: `domain`, `application`, `adapters.in`, `adapters.out`; no Spring or SQL under `domain/`
- [x] App uses database `afd` only; Compose on host port 3005

**Verification:**
- [x] `curl -sf localhost:3005/health`

**Dependencies:** Task 1, Task 3

**Files likely touched:**
- `agent-front-door/**`
- `docs/run/compose/docker-compose.yml`

**Estimated scope:** Medium

---

## Checkpoint: Foundation (after Tasks 1–7)

- [x] `docker compose up -d` — `/health` 200 on 3005, 3007, 3008, 3009
- [x] Control Plane is running as a catalogue UI on 3006; it has no database
- [x] Adminer login page on 8080 (`curl -sf -o /dev/null localhost:8080`)
- [x] Human review before contract endpoints

---

## Task 8: Capability PUT/GET by id@version

**Description:** Registry stores immutable published capability versions. Pipeline-shaped `PUT`; AR-shaped `GET`.

**Acceptance criteria:**
- [x] `PUT /v1/capabilities/{id}/versions/{version}` with workload auth upserts `draft`, publishes when `status=published`
- [x] Second `PUT` of the same published `(id, version)` returns 409
- [x] `GET` of a `draft` as AR (`X-Workload: ar`) fails closed (not 200)

**Verification:**
- [x] Tests pass: Registry capability publish/get/conflict
- [x] Manual: `curl` PUT then GET `account_fee_lookup` `1.0.0`

**Dependencies:** Task 2, Task 3

**Files likely touched:**
- `agent-capability-registry/src/main/resources/db/migration/V1__capabilities.sql`
- `agent-capability-registry/src/main/java/**/Capability*.java`
- `agent-capability-registry/src/test/java/**/Capability*Test.java`

**Estimated scope:** Medium

---

## Task 9: Manifest PUT/GET at named version

**Description:** Registry stores manifests as named `(manifest_id, manifest_version)` with tool refs. No `latest`. AR GETs the pinned pair.

**Acceptance criteria:**
- [x] `PUT`/`GET` for `fee_explain_v1` / `2026.08.1` with at least one tool ref to `account_fee_lookup@1.0.0`
- [x] GET missing version is 404; AR must not invent a latest
- [x] Published manifest is immutable (409 on overwrite)

**Verification:**
- [x] Tests pass: manifest get-at-pin
- [x] Manual: GET matches `docs/05-reference/manifest-fee-explain.json`

**Dependencies:** Task 8

**Files likely touched:**
- `agent-capability-registry/src/main/resources/db/migration/V2__manifests.sql`
- `agent-capability-registry/src/main/java/**/Manifest*.java`

**Estimated scope:** Medium

---

## Task 10: Registry contract tests

**Description:** Lock publish/get/409 behaviour so hydrate later cannot silently succeed on missing refs.

**Acceptance criteria:**
- [x] Tests fail if published overwrite succeeds
- [x] Tests fail if AR GET of draft returns the body
- [x] Seed helper can load Task 2 fixtures

**Verification:**
- [x] Tests in `agent-capability-registry` image build (`mvn test`)

**Dependencies:** Task 8, Task 9

**Files likely touched:**
- `agent-capability-registry/src/test/java/**`

**Estimated scope:** Small

---

## Task 11: Catalogue schema and seed `fee_explain`

**Description:** Data Plane stores versioned route rows with pointers only (manifest, policy, model, `agent_client_id`, `activation_target`). Seed the demo row.

**Acceptance criteria:**
- [x] Unique `(route_id, route_table_version)`
- [x] Seed `fee_explain` / `2026.08.1` plus playbook rows (`agent-account-v3`, payments, policy QA, chat, escalate): chat-visible, channel `web`, claim fields from the [route contract](https://jitendersharma.dev/playbooks/agents/intent-router/route-contract-reference); `activation_target` on fee_explain = Runtime `/v1/runs`
- [x] Pointers, not inlined `tools[]`; table version + `active` pointer per [lifecycle](https://jitendersharma.dev/playbooks/agents/intent-router/route-table-lifecycle)

**Verification:**
- [x] Flyway migration applies on `adp`
- [x] SQL / GET list returns the seeded rows after compose

**Dependencies:** Task 2, Task 4

**Files likely touched:**
- `agent-data-plane/src/main/resources/db/migration/V1__catalogue.sql`
- `agent-data-plane/src/main/resources/db/seed/fee_explain.sql`

**Estimated scope:** Medium

---

## Task 12: Eligible and catalogue-row GET

**Description:** Internal reads AFD and AR need: chips vs pinned pointers.

**Acceptance criteria:**
- [x] `GET /v1/intent/eligible` returns chat-visible ∩ claims ∩ channel (`fee_explain` for jane)
- [x] `GET /v1/catalog/routes` lists the active table; `GET /v1/catalog/routes/fee_explain?route_table_version=2026.08.1` returns pointers
- [x] AR workload may call catalogue GET; channel bearer is 401

**Verification:**
- [x] Tests pass: eligible + pinned row
- [x] `curl` with `X-Workload: afd` vs missing auth

**Dependencies:** Task 11

**Files likely touched:**
- `agent-data-plane/src/main/java/**/Eligible*.java`
- `agent-data-plane/src/main/java/**/Catalog*.java`

**Estimated scope:** Medium

---

## Task 13: Decide (entitle + Layer ① + Layer ② keywords)

**Description:** `POST /v1/intent/decide`. Intersect catalogue with claims and channel. Layer ① if `route_id` present. Layer ② keyword retrieve on the demo utterance. Outcomes `route` / `clarify` / `abstain`. No Layer ③. Only AFD may call decide.

**Acceptance criteria:**
- [x] Chat `$42` / fee message + jane claims → `outcome=route`, `route_id=fee_explain`, version `2026.08.1`
- [x] Empty eligible → `abstain`. Two close matches without a clear winner → `clarify` with candidates
- [x] `X-Workload: ar` on decide is 403

**Verification:**
- [x] Tests pass: route / clarify / abstain / forbidden caller
- [x] Manual: POST body from `docs/05-reference/decide-chat-route.json`

**Dependencies:** Task 12

**Files likely touched:**
- `agent-data-plane/src/main/java/**/Decide*.java`
- `agent-data-plane/src/test/java/**/Decide*Test.java`

**Estimated scope:** Medium

---

## Checkpoint: Decide (after Tasks 11–13)

- [x] Demo utterance routes to `fee_explain`
- [x] Catalogue GET at pin returns Runtime URL + manifest pointer
- [ ] Human review of keyword rules before Control Plane client wiring

---

## Task 14: Control Plane GETs routes / intent / catalogue from Data Plane

**Description:** Control Plane calls Data Plane HTTP for routes/intent/catalogue and serves a local catalogue UI on 3006. It does not receive audit, does not call decide, and has no database.

**Acceptance criteria:**
- [x] Client `GET /v1/intent/eligible` and `GET /v1/catalog/routes` + `GET /v1/catalog/routes/{id}` with `X-Workload: acp` succeed
- [x] Client does not call decide (AFD-only)
- [x] Catalogue UI on 3006 lists routes; clicking a route shows playbook field detail
- [x] Failure of Control Plane does not change decide

**Verification:**
- [x] `npm test` in `agent-control-plane`
- [x] Open `http://localhost:3006` — six seeded routes; fee_explain detail includes manifest pointer

**Dependencies:** Task 5, Task 12

**Files likely touched:**
- `agent-control-plane/src/data-plane-client.ts`

**Estimated scope:** Medium

---

## Task 15: Data Plane has no audit API or table

**Description:** Data Plane stays routes, intent, catalogue. No decision-audit store. No `/v1/decisions`.

**Acceptance criteria:**
- [x] `adp` has catalogue tables only — no `decisions` / audit table
- [x] `GET` or `POST /v1/decisions` is 404 (or unmapped)
- [x] Decide response is classify only (`route` / `clarify` / `abstain`); it does not write an audit log

**Verification:**
- [x] Tests pass: no decisions route; Flyway has no audit migration
- [x] Manual: decide still 200 (Control Plane is not on the decide path)

**Dependencies:** Task 13

**Files likely touched:**
- `agent-data-plane/src/main/resources/db/migration/**`
- `agent-data-plane/src/test/java/**`

**Estimated scope:** Medium

---

## Checkpoint: Control Plane client (after Tasks 14–15)

- [x] Control Plane fetched eligible + `fee_explain` catalogue row from Data Plane
- [x] No `/v1/decisions` on Data Plane
- [x] Decide does not fail when Control Plane is stopped
- [x] Catalogue UI lists playbook-shaped routes
- [ ] Review before AR start

---

## Task 16: AR start 202 and idempotency

**Description:** `POST /v1/runs` with `mode: new`. AFD workload only. Mint `correlation_id`. Unique `idempotency_key` returns the original id.

**Acceptance criteria:**
- [x] First start returns `202 { "correlation_id" }`
- [x] Same `idempotency_key` does not insert a second run pin
- [x] Channel bearer is 401

**Verification:**
- [x] `uv run pytest` idempotency test
- [x] `curl` twice with same key

**Dependencies:** Task 6, Task 2

**Files likely touched:**
- `agent-runtime/app/runs.py`
- `agent-runtime/alembic/versions/001_runs.py`

**Estimated scope:** Medium

---

## Task 17: Hydrate from Data Plane and Registry before 202

**Description:** Before `202`, AR GETs the catalogue row at the **pinned** version (never `active`) and GETs every manifest ref from Registry. Store `hydrated_tools` on the pin. Missing published ref → no `202`.

**Acceptance criteria:**
- [x] Successful start writes `hydrated_tools` in `ar`
- [x] Registry 404 / draft → controlled error to AFD, no `correlation_id`
- [x] AR does not call decide

**Verification:**
- [x] Tests pass: hydrate ok / missing ref
- [x] SQL: `hydrated_tools` nonempty on the pin

**Dependencies:** Task 9, Task 12, Task 16

**Files likely touched:**
- `agent-runtime/app/hydrate.py`
- `agent-runtime/app/clients/*.py`

**Estimated scope:** Medium

---

## Task 18: LangGraph stub complete, status GET, open-run

**Description:** After pin+hydrate, run a LangGraph graph whose stub node emits the canned fee message, then mark `completed`. AFD poll and freeze-miss reconciliation.

**Acceptance criteria:**
- [x] `GET /v1/runs/{correlation_id}` returns slim status + result (pack shape)
- [x] Completion goes through a LangGraph graph, not a direct SQL status update from the HTTP handler
- [x] No Kafka; no live model; no domain HTTP invoke

**Verification:**
- [x] `uv run pytest` status + open-run + graph stub node
- [x] Manual: start then GET matches canned string

**Dependencies:** Task 17

**Files likely touched:**
- `agent-runtime/app/graph.py`
- `agent-runtime/app/runs.py`

**Estimated scope:** Medium

---

## Checkpoint: AR (after Tasks 16–18)

- [x] Start → 202 → GET completed canned message
- [x] Duplicate key: one row in `ar`
- [x] Missing capability: no 202
- [ ] Review before jobs on Front Door

---

## Task 30: Jobs HTTP on the same Front Door process

**Description:** After AR start/hydrate/status (Tasks 16–18). Same Front Door process and port 3005. `/v1/jobs` sits next to chat `/v1/assistant/*` (chat APIs land later). Do **not** add a second fleet, hostname, or Compose service. Jobs name `route_id`, call Data Plane Layer ① (entitle + bind, no keyword classify, no `clarify`), freeze, start AR, return `202 { "correlation_id" }`. Callers may see `route_id` / `correlation_id` (FR-5 is chat-only).

**Acceptance criteria:**
- [x] `POST /v1/jobs` with `route_id=fee_explain`, jane claims, and `idempotency_key` → `202` + `correlation_id`
- [x] Decide body uses `ingress: "jobs"` and explicit `route_id`; no Layer ②; never returns chat `clarify` to the jobs caller (missing claims / unknown route → fail closed, do not start)
- [x] `GET /v1/jobs/{correlation_id}` polls AR HTTP status (same as events, no Data Plane call)
- [x] Duplicate `idempotency_key` returns the original `correlation_id` (no second AR `mode: new`)
- [x] One Java process still serves `/v1/assistant/*` and `/v1/jobs*`

**Verification:**
- [x] Tests pass: jobs start, entitle miss, idempotent replay, GET status
- [x] Manual: `POST :3005/v1/jobs` then GET until canned fee message
- [x] Compose still has a single `agent-front-door` service

**Dependencies:** Task 18

**Files likely touched:**
- `agent-front-door/src/main/java/**/Jobs*.java`
- `agent-front-door/src/test/java/**/Jobs*Test.java`
- `docs/05-reference/decide-jobs-route.json`
- `docs/05-reference/jobs-start.json`

**Estimated scope:** Medium

---

## Task 31: Jobs demo and handbook update

**Description:** Scripted jobs proof on the same Front Door process. Chat demo stays Task 23 and is chat-only. Document jobs APIs now; root README covering both route families is Task 24 after chat.

**Acceptance criteria:**
- [x] `docs/run/dummy-request/job/1-autonomous/fee_explain.sh` proves `POST /v1/jobs` for `fee_explain` and GET until the canned fee message
- [x] Front Door README documents `POST /v1/jobs` and `GET /v1/jobs/{correlation_id}`; Layer ①; still one process, no second fleet
- [x] Demo is idempotent (same jobs key twice still exits 0)

**Verification:**
- [x] Demo exits 0 twice (idempotent jobs key)
- [x] Manual: Front Door handbook matches the running jobs routes

**Dependencies:** Task 18, Task 30

**Files likely touched:**
- `docs/run/dummy-request/job/1-autonomous/fee_explain.sh`
- `agent-front-door/README.md`

**Estimated scope:** Small

---

## Checkpoint: Jobs path (after Tasks 30–31)

- [x] `POST /v1/jobs` + GET completed canned message on the same Front Door process
- [x] Jobs skip classify; missing claims do not start AR
- [x] Still one AFD process (no second fleet)
- [x] Front Door handbook matches the jobs routes
- [x] Review before chat path

---

## Task 19: AFD freeze table and session mint

**Description:** Front Door owns `session_id` and the frozen route/session row (TTL 30–60 min). Not the catalogue, not the run pin. Chat path — after jobs.

**Acceptance criteria:**
- [x] New chat mints `session_id`
- [x] Freeze stores `route_id`, versions, `activation_target`, `agent_client_id`, later `correlation_id`
- [x] Pin miss does not query AR SQL (only AR HTTP)

**Verification:**
- [x] Tests pass: session mint + freeze write
- [x] Row in database `afd`

**Dependencies:** Task 7, Task 18

**Files likely touched:**
- `agent-front-door/src/main/resources/db/migration/V1__freeze.sql`
- `agent-front-door/src/main/java/**/Session*.java`

**Estimated scope:** Medium

---

## Task 20: Hints and turn (decide → freeze → start)

**Description:** Chat AFD public API. Hints from eligible. New turn calls decide; on `route` reads catalogue row, writes freeze, starts AR, returns slim `accepted`. Never leak FR-5 fields.

**Acceptance criteria:**
- [x] `GET /v1/assistant/hints` returns labels + opaque `hint_id` only
- [x] `POST /v1/assistant/turns` with demo message → `{ session_id, status: "accepted" }`
- [x] Response (and events payload) have none of `route_id`, `run_id`, `agent_client_id`, `confidence`, `router_layer`

**Verification:**
- [x] Tests pass: slim JSON + forbidden-key scanner
- [x] Manual: turn with stub jane claims

**Dependencies:** Task 13, Task 17, Task 19

**Files likely touched:**
- `agent-front-door/src/main/java/**/Assistant*.java`
- `agent-front-door/src/test/java/**/Fr5*Test.java`

**Estimated scope:** Medium

---

## Task 21: Poll events until AR completed

**Description:** `GET /v1/assistant/sessions/{session_id}/events` polls AR HTTP status and returns slim tokens/final message. Kafka/`{runs_topic}` and SSE are out of scope.

**Acceptance criteria:**
- [x] After accepted turn, poll returns `completed` + canned user-visible message
- [x] AFD does not call Data Plane on this GET
- [x] Slim JSON still obeys FR-5

**Verification:**
- [x] Tests pass: poll completed
- [x] Manual: turn then poll

**Dependencies:** Task 18, Task 20

**Files likely touched:**
- `agent-front-door/src/main/java/**/Events*.java`

**Estimated scope:** Medium

---

## Task 22: Continuation skips decide

**Description:** Second `POST /v1/assistant/turns` on a frozen session (`"yes"` / follow-up) resumes AR `POST /v1/runs/{id}/turns` and does not call decide.

**Acceptance criteria:**
- [x] Continuation does not call Data Plane decide (AFD unit/integration test)
- [x] Resume hits AR turns path; no second `POST /v1/runs` with `mode: new`
- [x] Freeze TTL miss uses `GET /v1/runs?session_id=` then resume (not AR SQL)

**Verification:**
- [x] Tests pass: skip decide + resume
- [x] Manual: two turns; second does not POST decide

**Dependencies:** Task 21, Task 18

**Files likely touched:**
- `agent-front-door/src/main/java/**/Assistant*.java`
- `agent-runtime/app/runs.py`

**Estimated scope:** Medium

---

## Checkpoint: Chat path (after Tasks 19–22)

- [x] Hints → turn → poll completed
- [x] FR-5 holds on turn and events
- [x] Continuation does not classify
- [x] Human review before demo script

---

## Task 23: Demo script and four-DB assertions

**Description:** One script is the plan’s success check: compose is up, seed is loaded, one chat turn, four Postgres databases written, Control Plane fetched catalogue/eligible from Data Plane.

**Acceptance criteria:**
- [x] `docs/run/scripts/demo-chat-turn.sh` exits 0 only if slim completed message matches canned text
- [x] Script fails if any of `afd` / `adp` / `ar` / `acr` lacks the expected row
- [x] Script fails if Control Plane did not successfully GET eligible and the `fee_explain` catalogue row
- [x] Seed is idempotent (`compose` or script can reload `fee_explain` + capability + manifest)

**Verification:**
- [x] `docker compose up -d && ./docs/run/scripts/demo-chat-turn.sh`
- [x] Run twice: still exit 0 (idempotent start keys / seeds)

**Dependencies:** Task 10, Task 22

**Files likely touched:**
- `docs/run/scripts/demo-chat-turn.sh`
- `docs/run/scripts/seed-db.sh`

**Estimated scope:** Medium

---

## Task 25: Registry service handbook

**Description:** `agent-capability-registry/README.md` explains this box as built: publish/get, immutability, schema, who may call it.

**Acceptance criteria:**
- [x] Headings: job, port/stack, hexagonal layout, auth, APIs, contracts, tables/schema, sibling calls, non-goals, tests
- [x] Documents `PUT`/`GET` capability and manifest paths, 409 on published overwrite, AR cannot GET draft
- [x] Documents `acr` tables, keys `(id, version)` and `(manifest_id, manifest_version)`, and seed `account_fee_lookup@1.0.0`

**Verification:**
- [x] Manual: every path and table in the README exists in code/migrations

**Dependencies:** Task 10

**Files likely touched:**
- `agent-capability-registry/README.md`

**Estimated scope:** Small

---

## Task 26: Data Plane service handbook

**Description:** `agent-data-plane/README.md` explains eligible, decide, catalogue row (manifest pointers), and `adp` schema. No audit.

**Acceptance criteria:**
- [x] Same heading set as Task 25
- [x] Documents decide / eligible / catalogue APIs, Layer ①/②, outcomes `route`/`clarify`/`abstain`; AR must not call decide; Control Plane may GET eligible and catalogue
- [x] Documents catalogue tables only; explicitly **no** decisions/audit API or table

**Verification:**
- [x] Manual: README matches running Data Plane and Flyway files

**Dependencies:** Task 15

**Files likely touched:**
- `agent-data-plane/README.md`

**Estimated scope:** Small

---

## Task 27: Control Plane service handbook

**Description:** `agent-control-plane/README.md` explains the TypeScript client: no APIs, no database, calls Data Plane for routes/intent/catalogue.

**Acceptance criteria:**
- [x] Same heading set; APIs section is **none**; schema section is **no database**
- [x] Documents outbound `GET /v1/intent/eligible` and `GET /v1/catalog/routes/{route_id}` with `X-Workload: acp`
- [x] Documents that decide is AFD-only and that this process is not on the chat hot path

**Verification:**
- [x] Manual: README matches the client; no invented Fastify routes or SQL

**Dependencies:** Task 14

**Files likely touched:**
- `agent-control-plane/README.md`

**Estimated scope:** Small

---

## Task 28: Runtime service handbook

**Description:** `agent-runtime/README.md` explains start, hydrate, LangGraph stub graph, run pin schema, uv commands.

**Acceptance criteria:**
- [x] Same heading set; stack is uv + FastAPI + LangGraph
- [x] Documents `/v1/runs`, turns, status, open-run by `session_id`, idempotency, hydrate-before-202
- [x] Documents `ar` tables (`correlation_id`, `idempotency_key`, `hydrated_tools`, checkpoint/status) and LLM via env (stub or provider — not “never a model”)

**Verification:**
- [x] Manual: README matches FastAPI routes, Alembic, and graph modules

**Dependencies:** Task 18

**Files likely touched:**
- `agent-runtime/README.md`

**Estimated scope:** Small

---

## Task 29: Front Door service handbook

**Description:** `agent-front-door/README.md` adds chat AFD: hints, turns, events poll, freeze table, FR-5, sibling call map. Jobs routes are already documented in Task 31.

**Acceptance criteria:**
- [x] Same heading set; hexagonal layout; chat `/v1/assistant/*` and jobs `/v1/jobs*` on 3005 (one process)
- [x] Documents `/v1/assistant/hints`, `turns`, `events`; slim JSON; continuation skips decide
- [x] Documents `afd` freeze table fields, TTL, and that pin miss uses AR HTTP not AR SQL

**Verification:**
- [x] Manual: README matches AFD APIs and Flyway; forbidden keys listed

**Dependencies:** Task 22, Task 31

**Files likely touched:**
- `agent-front-door/README.md`

**Estimated scope:** Small

---

## Task 24: Root README for compose, ports, demo

**Description:** Short run instructions only — not a restatement of the architecture packs. Links to the five service handbooks. Mentions both `/v1/assistant/*` and `/v1/jobs*` on 3005.

**Acceptance criteria:**
- [x] README lists HTTP ports 3005 / 3007 / 3008 / 3009, Control Plane UI 3006, and the five folders
- [x] Commands: compose up, seed, jobs demo, chat demo; stubs: Kafka, IdP, LLM (decide ③ off)
- [x] Links to each service `README.md`; both route families on 3005

**Verification:**
- [x] Manual: a new session can follow README without this chat

**Dependencies:** Task 23, Task 31, Tasks 25–29

**Files likely touched:**
- `README.md`

**Estimated scope:** Small

---

## Checkpoint: Complete

- [x] `./docs/run/dummy-request/run-job.sh fee_explain` and `./docs/run/dummy-request/run-chat.sh fee_explain` pass on a clean compose
- [x] Per-service tests pass (Runtime pytest; Control Plane `npm test`; spot-check)
- [x] Each of the five service `README.md` files matches running APIs and schemas
- [x] Out of scope still out (no Kafka, no second AFD fleet; decide Layer ③ off)
- [x] Human approves (2026-08-26) — handbooks 24–29 + checkpoint
