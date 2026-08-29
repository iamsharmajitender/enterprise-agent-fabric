# Task list: Agent audit (local Fabric)

Plan: [audit-plan.md](./audit-plan.md). Docs map: [README.md](../README.md). Parked summary: [future-enhancement.md](./future-enhancement.md#3-audit--decision-record--evidence-chain).

**Execution order:**

1. **Foundation** — A1–A4. Envelope, DB `audit`, service scaffolds, Compose.
2. **Phase A — AADP** — A5–A7. Append-only store + ingest + query.
3. **Phase A — producers** — A8–A11. Async HTTP clients; ADP / AFD / AR emit.
4. **Phase A — AACP** — A12. Lookup UI for `fee_explain` chain.
5. **Phase B** — A13–A16. Stage digests, ACR publish, AACP timeline, retention/redaction docs.
6. **Later (parked)** — A17–A18. Kafka; optional outbox.

v1 fabric tasks remain in [todo.md](./todo.md); observability remains in [observability-todo.md](./observability-todo.md) (ops ≠ audit); evals / intent / dataflow lists do not replace this track.

Dummy jobs returning `completed` without audit rows is **not** acceptance for Phase A+.

**Ports:** AADP **3012**, AACP **3013** (`agent-mocks` keeps **3010**).

---

## 0. Foundation

## Task A1: Event envelope schema + reference JSON

**Description:** Freeze the audit event envelope and one example per Phase A `event_type` under `agent-fabric-docs/05-reference/`. Document allowlisted payload fields and default-deny (no raw utterance, claims JSON, tokens).

**Acceptance criteria:**
- [x] JSON Schema (or checked examples + field table) for envelope: `event_id`, `event_type`, `occurred_at`, `producer`, `correlation_id`, `session_id`, `decision_id`, `payload`
- [x] Examples for `decide.completed`, `freeze.written` (or `pin.started`), `hydrate.snapshot`, `run.terminal`
- [x] README or plan cross-link states Phase B types (`stage.*`, `*.published`) without requiring full examples yet
- [x] Explicit: chat FR-5 wire JSON does not grow audit fields

**Verification:**
- [x] Manual: a new session can mint a valid event by copying an example
- [x] Field table matches [audit-plan.md](./audit-plan.md) envelope section

**Dependencies:** None

**Files likely touched:**
- `agent-fabric-docs/05-reference/audit-event-envelope.json` (and/or per-type examples)
- `agent-fabric-docs/tasks/audit-plan.md` (link only if needed)

**Estimated scope:** Small

---

## Task A2: Postgres database `audit` in Compose init

**Description:** Create database `audit` on the shared Postgres 16 server alongside `afd`, `adp`, `ar`, `acr`. No tables yet (Flyway in A5).

**Acceptance criteria:**
- [x] `agent-fabric-scripts/docker-compose/init-postgres.sql` creates `audit`
- [x] Compose / Dockerfile.postgres path still bootstraps all five DBs on fresh volume
- [x] Adminer can connect to `audit` as user `fabric`

**Verification:**
- [x] Fresh `docker compose` volume: `\l` or Adminer shows `audit`
- [x] Existing four DBs unchanged

**Dependencies:** None

**Files likely touched:**
- `agent-fabric-scripts/docker-compose/init-postgres.sql`
- `agent-fabric-scripts/docker-compose/docker-compose.yml` (labels/comments if any)

**Estimated scope:** Small

---

## Task A3: Scaffold `agent-audit-data-plane` (Java hexagonal)

**Description:** New service folder mirroring ADP shape enough to boot: Spring Boot 3, Java 21, health on **3012**, Flyway placeholder, README stating append-only ingest + query; no producer logic.

**Acceptance criteria:**
- [x] `agent-audit-data-plane/` builds and exposes `GET /health` (or actuator health)
- [x] README: port 3012, DB `audit`, boundaries (producers POST; AACP GET; no decide/start)
- [x] Workload header convention documented (`X-Workload`)
- [x] Unit/smoke test: context loads or health test

**Verification:**
- [x] `./mvnw test` (or project equivalent) passes in the new module
- [x] Local jar/boot responds on 3012 when run against `audit` DB

**Dependencies:** Task A2 (DB exists for local run)

**Files likely touched:**
- `agent-audit-data-plane/**`
- `agent-fabric-scripts/docker-compose/docker-compose.yml` (service stub may wait for A4)

**Estimated scope:** Medium

---

## Task A4: Scaffold `agent-audit-control-plane` + Compose wiring

**Description:** TypeScript control UI/client on **3013** (ACP-like): no database; `AUDIT_DATA_PLANE_URL` only. Wire both audit boxes into Compose with OTEL env parity; document ports in `.env.example`.

**Acceptance criteria:**
- [x] `agent-audit-control-plane/` serves a minimal page or health on 3013
- [x] Compose services `agent-audit-data-plane` (:3012) and `agent-audit-control-plane` (:3013); AADP uses JDBC to `audit`
- [x] `.env.example` lists `AADP_PORT=3012`, `AACP_PORT=3013`, `AUDIT_DATA_PLANE_URL`
- [x] READMEs note AACP never talks to ADP/AR/AFD for audit data

**Verification:**
- [x] `docker compose … config` shows both services
- [x] `./agent-fabric-scripts/stack/start-app.sh` brings AADP + AACP up (ingest may still be stub)

**Dependencies:** Task A3

**Files likely touched:**
- `agent-audit-control-plane/**`
- `agent-fabric-scripts/docker-compose/docker-compose.yml`
- `agent-fabric-scripts/docker-compose/.env.example`

**Estimated scope:** Medium

---

## Checkpoint: Foundation

- [x] A1–A4 done
- [x] Envelope examples + DB `audit` + both boxes boot on 3012/3013
- [x] Human review before Phase A ingest schema

---

## 1. Phase A — AADP

## Task A5: Flyway events table (append-only)

**Description:** Migration `V1__audit.sql` (or similar): events table keyed by `event_id`, columns for envelope + `payload` JSONB, indexes on `correlation_id`, `session_id`, `occurred_at`, `event_type`. No UPDATE API in application code.

**Acceptance criteria:**
- [x] Unique primary key on `event_id`
- [x] Indexes support chain-by-correlation and session lookup
- [x] README or comment: application must not expose update/delete of event rows (redaction policy later)

**Verification:**
- [x] Flyway migrates clean on empty `audit`
- [x] Duplicate `event_id` insert fails at DB or is upsert-no-op per A6 design

**Dependencies:** Task A2, A3

**Files likely touched:**
- `agent-audit-data-plane/src/main/resources/db/migration/V1__audit.sql`

**Estimated scope:** Small

---

## Task A6: `POST /v1/audit/events` ingest

**Description:** Append-only HTTP ingest. Validate envelope; persist; idempotent on `event_id` (duplicate → 200 with same resource). Do not block callers beyond normal HTTP (producers will be async).

**Acceptance criteria:**
- [x] `POST /v1/audit/events` accepts Phase A event types
- [x] Invalid envelope → 4xx; no partial row
- [x] Duplicate `event_id` → idempotent success (no second semantic event)
- [x] Reject payloads with known deny keys if present at top level (utterance, Authorization) — document allowlist
- [x] Tests for happy path + duplicate + validation

**Verification:**
- [x] `curl` POST then GET chain (A7) or direct SQL shows one row
- [x] Unit/WebTestClient coverage

**Dependencies:** Task A1, A5

**Files likely touched:**
- `agent-audit-data-plane/src/main/java/**`
- `agent-audit-data-plane/src/test/java/**`

**Estimated scope:** Medium

---

## Task A7: Query APIs by correlation_id and session_id

**Description:** Read APIs for ops: ordered event chain for a run and for a session/job freeze key. Optional filtered list by time/`event_type`.

**Acceptance criteria:**
- [x] `GET /v1/audit/chains/{correlation_id}` returns events ordered by `occurred_at` (then insert order)
- [x] `GET /v1/audit/sessions/{session_id}` returns matching events
- [x] Empty chain → 200 `[]` or 404 documented; consistent choice
- [x] Tests with multiple event types for one correlation

**Verification:**
- [x] Insert decide + pin + hydrate + terminal → chain returns four in order
- [x] Wrong id → empty/404 as documented

**Dependencies:** Task A6

**Files likely touched:**
- `agent-audit-data-plane/src/main/java/**`
- `agent-audit-data-plane/src/test/java/**`
- `agent-fabric-docs/05-reference/` (optional response examples)

**Estimated scope:** Medium

---

## Checkpoint: Phase A store

- [x] A5–A7 done
- [x] Manual POST of Phase A examples round-trips through query
- [x] Human review before producer wiring

---

## 2. Phase A — producers

## Task A8: Shared async audit client (Java + Python)

**Description:** Non-blocking emit helpers: enqueue or async HTTP POST to AADP; never throw into decide/start hot path; metric/counter on failure or drop. Config: `AUDIT_DATA_PLANE_URL` (optional disable for unit tests).

**Acceptance criteria:**
- [x] Java helper usable from AFD / ADP / ACR (module or small shared pattern per service)
- [x] Python helper usable from AR
- [x] Timeout short; failures logged + metric; caller continues
- [x] When URL unset/disabled, no-op success (local unit tests)

**Verification:**
- [x] Unit test: mock server down → caller method still returns normally
- [x] Unit test: mock 202/200 → event received

**Dependencies:** Task A6

**Files likely touched:**
- `agent-front-door/...` and/or small shared lib
- `agent-data-plane/...`
- `agent-runtime/app/**`
- `agent-capability-registry/...` (client ready for Phase B)

**Estimated scope:** Medium

---

## Task A9: ADP emits `decide.*`

**Description:** After decide result is known, async-emit `decide.completed` / clarify / abstain with allowlisted payload (`outcome`, route pin when present, candidate ids, `router_layer`, hashes, channel, ingress). Mint `decision_id` for join.

**Acceptance criteria:**
- [x] Chat and jobs decide paths emit once per decide call
- [x] No utterance text or raw claims in payload
- [x] Decide latency / success unchanged when AADP down
- [x] Test: decide → event captured (WireMock / in-memory)

**Verification:**
- [x] fee_explain decide in Compose → row in `audit` with matching hashes/layer
- [x] AADP stopped → assistant/jobs still 2xx/202 path as today

**Dependencies:** Task A8, A7

**Files likely touched:**
- `agent-data-plane/src/main/java/**/DecideService*` (or adapter after decide)
- `agent-data-plane/src/test/java/**`

**Estimated scope:** Medium

---

## Task A10: AFD emits `freeze.*` / `pin.*`

**Description:** When freeze is written and Runtime start returns `correlation_id`, async-emit freeze/pin events linking `session_id` / job key, `route_id@version`, `correlation_id`, optional `decision_id`.

**Acceptance criteria:**
- [x] Chat and jobs paths emit
- [x] Duplicate freeze reuse (idempotent session) does not invent a second conflicting pin story (document: emit once per new correlation or include correlation in event)
- [x] Fail-open if AADP down
- [x] Tests for emit fields

**Verification:**
- [x] End-to-end fee_explain: decide + freeze/pin rows share join ids
- [x] FR-5 chat body still free of `route_id` / audit fields

**Dependencies:** Task A8, A9 helpful for `decision_id`

**Files likely touched:**
- `agent-front-door/src/main/java/**`
- `agent-front-door/src/test/java/**`

**Estimated scope:** Medium

---

## Task A11: AR emits `hydrate.snapshot` + `run.terminal`

**Description:** After successful hydrate, emit snapshot (capability pins + digests). On terminal status (`completed` / `failed` / `waiting`), emit `run.terminal`. Async; fail-open.

**Acceptance criteria:**
- [x] Hydrate failure (422) does not emit a successful snapshot; may emit nothing or explicit failure type (document choice)
- [x] Terminal covers waiting (human_gate) as well as completed/failed
- [x] Payload has no raw tool bodies
- [x] Tests with in-memory audit client

**Verification:**
- [x] fee_explain run: hydrate + terminal visible in AADP chain for `correlation_id`
- [x] AADP down → run still completes

**Dependencies:** Task A8, A7

**Files likely touched:**
- `agent-runtime/app/agents/hydrate.py` / `agent_core.py` / `execution.py`
- `agent-runtime/tests/**`

**Estimated scope:** Medium

---

## Checkpoint: Phase A producers

- [x] A8–A11 done
- [x] One fee_explain journey: decide → freeze/pin → hydrate → terminal in `GET .../chains/{correlation_id}`
- [x] Fail-open proven with AADP stopped

---

## 3. Phase A — AACP

## Task A12: AACP lookup UI by correlation_id

**Description:** Minimal control UI: input `correlation_id` (and optionally `session_id`), call AADP query APIs, render ordered Phase A events. No catalogue/decide.

**Acceptance criteria:**
- [x] Page on :3013 shows chain for a known correlation after fee_explain demo
- [x] Uses `AUDIT_DATA_PLANE_URL` only
- [x] Empty/error states when AADP down or unknown id
- [x] README: how to demo

**Verification:**
- [x] Manual: copy `correlation_id` from jobs/chat accept → AACP shows Phase A four-event story
- [x] Smoke test or playwright optional; at least fetch client unit test

**Dependencies:** Task A7, A11

**Files likely touched:**
- `agent-audit-control-plane/**`

**Estimated scope:** Medium

---

## Checkpoint: Phase A done

- [x] A1–A12 done
- [x] Demo path in [audit-plan.md](./audit-plan.md) works for Phase A
- [x] Human review before Phase B

---

## 4. Phase B

## Task A13: AR emits `stage.*` digests

**Description:** After each graph stage (or on stage completion), async-emit `stage.completed` / `stage.failed` with `stage_id`, latency, request/response digests (not full bodies by default).

**Acceptance criteria:**
- [x] Linear and branched routes emit per executed stage
- [x] human_gate waiting still consistent with terminal + stage events
- [x] Deny raw HTTP bodies in default payload
- [x] Tests for at least one multi-stage route

**Verification:**
- [x] Chain for a multi-stage job includes ordered `stage.*` between hydrate and terminal
- [x] Fail-open preserved

**Dependencies:** Task A11, Phase A checkpoint

**Files likely touched:**
- `agent-runtime/app/graph/workflow.py` / execution hooks
- `agent-runtime/tests/**`
- `agent-fabric-docs/05-reference/` (stage event example)

**Estimated scope:** Medium

---

## Task A14: ACR emits `capability.published` / `manifest.published`

**Description:** On publish/create paths that introduce a new capability or manifest version (seed load or admin API if present), async-emit provenance events with id, version, content digest. Not on every runtime GET.

**Acceptance criteria:**
- [x] Publish/seed path emits; hydrate GET does not spam publish events
- [x] Payload allowlisted
- [x] Fail-open
- [x] Test with stub client

**Verification:**
- [x] Fresh registry migrate/seed → publish events queryable (or documented hook point if seed is SQL-only: emit from a controlled bootstrap or defer to first Admin API)
- [x] Document SQL-seed limitation if emit is API-only

**Dependencies:** Task A8

**Files likely touched:**
- `agent-capability-registry/src/main/java/**`
- `agent-capability-registry/src/test/java/**`

**Estimated scope:** Medium

---

## Task A15: AACP timeline includes stages (+ optional publish)

**Description:** Extend AACP chain view: show `stage.*` in order; optional filter or side panel for ACR publish events related to hydrated caps.

**Acceptance criteria:**
- [x] Phase B demo: multi-stage run shows stages in UI
- [x] Phase A-only chains still render
- [x] README updated

**Verification:**
- [x] Manual screenshot or scripted check against AADP fixtures

**Dependencies:** Task A12, A13

**Files likely touched:**
- `agent-audit-control-plane/**`

**Estimated scope:** Small

---

## Task A16: Retention + redaction policy defaults (local)

**Description:** Document and (lightly) implement local defaults: retention window for `audit` events; redaction rules (hash algorithms, digest canonicalization). No full legal-hold product.

**Acceptance criteria:**
- [x] Doc section in AADP README or `agent-fabric-docs/02-understand/` / plan appendix: retention default (e.g. 30d local), deny-list, hash fields
- [x] Optional: scheduled delete/archive job stub or SQL note for local GC
- [x] Aligns with envelope deny-list from A1

**Verification:**
- [x] Manual: policy readable by a new engineer in one pass
- [x] No raw utterance in any Phase A/B fixture

**Dependencies:** Task A1, A7

**Files likely touched:**
- `agent-audit-data-plane/README.md`
- `agent-fabric-docs/tasks/audit-plan.md` (pointer)
- optional GC migration/job

**Estimated scope:** Small

---

## Checkpoint: Phase B done

- [x] A13–A16 done
- [x] fee_explain or multi-stage job: full chain including stages in AACP
- [x] Publish provenance path documented/proven
- [x] Human review

---

## 5. Later (parked — not blocking Phase A/B)

## Task A17: Kafka transport (same envelope)

**Description:** Producers publish envelope to `{audit_events}` (or equivalent); AADP consumes and appends. HTTP ingest remains for backfill and local without Kafka. Decide/start still must not await bus ack on the hot path (producer send async).

**Acceptance criteria:**
- [ ] Envelope bytes identical to HTTP body schema
- [ ] Compose profile or doc for Kafka optional locally
- [ ] Consumer idempotent on `event_id`
- [ ] HTTP path still works with Kafka off

**Verification:**
- [ ] Integration test or manual: produce → consume → chain query
- [ ] Fail-open / lag metrics documented

**Dependencies:** Phase A checkpoint; real or testcontainers Kafka

**Files likely touched:**
- `agent-audit-data-plane/**`
- producers’ audit clients
- `agent-fabric-scripts/docker-compose/docker-compose.yml`

**Estimated scope:** Large

---

## Task A18: Producer outbox (almost no loss)

**Description:** Optional transactional outbox in producer DBs for audit events when “best-effort async HTTP” is insufficient. Relay to HTTP or Kafka. Only after A17 or explicit durability requirement.

**Acceptance criteria:**
- [ ] Outbox table + relay for at least one producer (recommend AFD or ADP first)
- [ ] At-least-once delivery; AADP idempotent on `event_id`
- [ ] Document when to enable vs plain async HTTP

**Verification:**
- [ ] Kill AADP during decide; restart; relay drains; chain complete
- [ ] No double semantic events for same `event_id`

**Dependencies:** Task A17 or explicit product ask

**Files likely touched:**
- producer Flyway + relay
- `agent-fabric-docs/tasks/audit-plan.md` (durability note)

**Estimated scope:** Large

---

## Packaging note

When A1–A16 are signed off, add a one-line “Done” entry under **Active follow-on** / **Done** in [future-enhancement.md](./future-enhancement.md) and keep A17–A18 parked there or in this file’s section 5.
