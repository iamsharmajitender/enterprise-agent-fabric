# Task list: Three-layer observability (local Fabric)

Plan: [observability-plan.md](./observability-plan.md). Docs map: [docs/README.md](../README.md). Blueprint: [Observability: Three Layers, One Graph](https://jitendersharma.dev/blueprints/observability-blueprint).

**Execution order:** O1 → O3 (foundation), then O4–O7 (Layer ② path), checkpoint, then O9–O11 (Layer ①), O12–O13 (Layer ③), O14–O16 (intelligence). O8 is optional after O7.

v1 fabric tasks remain in [todo.md](./todo.md); evals remain in [eval-todo.md](./eval-todo.md); intent remains in [intent-todo.md](./intent-todo.md); stage data sharing remains in [dataflow-todo.md](./dataflow-todo.md). This list does not replace them.

---

## Task O1: OTEL env + depends on otel-lgtm for all app services

**Description:** Wire every Fabric app service in Compose to export OTLP to the existing `otel-lgtm` container, with unique `OTEL_SERVICE_NAME` and local-friendly metric export interval. No SDK code required yet — env and dependency graph only.

**Acceptance criteria:**
- [x] `agent-front-door`, `agent-data-plane`, `agent-runtime`, `agent-capability-registry`, and `agent-control-plane` set `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-lgtm:4318`, `OTEL_METRIC_EXPORT_INTERVAL=500`, and `OTEL_RESOURCE_ATTRIBUTES` including `service.namespace=agent-fabric` and `deployment.environment=local`
- [x] Each of those services `depends_on` `otel-lgtm` (service_started is enough)
- [x] README Observability section notes that env is set and SDKs land in later tasks

**Verification:**
- [x] `docker compose -f docs/run/compose/docker-compose.yml config` shows OTEL vars on app services
- [x] `./docs/run/scripts/start-app.sh` still brings stack up; `curl -sf localhost:3005/health` (and siblings) succeed

**Dependencies:** None

**Files likely touched:**
- `docs/run/compose/docker-compose.yml`
- `README.md`

**Estimated scope:** Small

---

## Task O2: Structured JSON logging baseline (Java + Python)

**Description:** Ensure app logs are machine-parseable JSON (or Logback/JSON encoder / Python structured logger) so Loki queries can filter by `event`, `service`, and correlation fields once IDs exist.

**Acceptance criteria:**
- [x] Front Door, Data Plane, Registry emit JSON logs to stdout in Compose
- [x] Runtime emits JSON (or structured key=value that Loki can parse) to stdout
- [x] Log lines use stable fields where events already exist (`job_accepted`, warnings); no raw `Authorization` or `X-Stub-Claims`

**Verification:**
- [x] `docker compose -f docs/run/compose/docker-compose.yml logs agent-front-door` shows parseable JSON (or documented format)
- [x] Spot-check: no bearer tokens in log output after a jobs or health call

**Dependencies:** None (can parallel O1)

**Files likely touched:**
- `agent-front-door/src/main/resources/application.yml` (and/or `logback-spring.xml`)
- `agent-data-plane/src/main/resources/**`
- `agent-capability-registry/src/main/resources/**`
- `agent-runtime/app/main.py` (or logging config module)

**Estimated scope:** Medium

---

## Task O3: AFD request ID / traceparent accept-or-mint at channel edge

**Description:** At channel ingress, accept inbound `traceparent` / `X-Request-Id` or mint them; put request id on the response and on a request-scoped logger MDC so later OTel and business events share an edge id before `correlation_id` exists.

**Acceptance criteria:**
- [x] Unauthenticated health remains unchanged
- [x] Channel requests get a stable request id (header echo) when missing
- [x] Inbound W3C `traceparent` is preserved when present (ready for O4 propagator)
- [x] MDC (or equivalent) includes `request_id` on AFD logs for that request

**Verification:**
- [x] Unit/filter test: missing id → response has id; provided id → echoed
- [x] Manual: `curl -i` assistant or jobs path shows request id header

**Dependencies:** Task O2 helpful but not required

**Files likely touched:**
- `agent-front-door/src/main/java/**/adapters/in/http/**`
- `agent-front-door/src/test/java/**`

**Estimated scope:** Small

---

## Checkpoint: Foundation

- [x] O1–O3 done
- [x] Stack boots; JSON logs from at least AFD and AR
- [ ] Human review before SDK dependency work

---

## Task O4: Front Door OTel + RestClient propagation

**Description:** Add OpenTelemetry to Front Door so inbound HTTP and outbound RestClient calls to Data Plane and Runtime continue the same trace. Resource `service.name=agent-front-door`.

**Acceptance criteria:**
- [x] OTel (or Boot OTel starter) on the classpath; agent or SDK starts with the app
- [x] Outbound decide, catalogue, and runtime clients propagate W3C context
- [x] Span attributes may include `session_id`, `route_id`, `route_version` where known — not utterance or claims
- [x] RED (or OTel HTTP metrics) visible for inbound channel routes after traffic

**Verification:**
- [x] `mvn test` in Front Door passes
- [x] After demo traffic, Tempo shows spans for `agent-front-door` with child calls toward ADP/AR

**Dependencies:** Task O1, Task O3

**Files likely touched:**
- `agent-front-door/pom.xml`
- `agent-front-door/src/main/java/**/bootstrap/**`
- `agent-front-door/src/main/java/**/adapters/out/http/**`
- `docs/run/compose/docker-compose.yml` (any extra Java OTEL agent env if used)

**Estimated scope:** Medium

---

## Task O5: Data Plane OTel + decide / catalog / JDBC

**Description:** Instrument Data Plane so `/v1/intent/decide` and catalogue reads appear in the parent AFD trace, with JDBC as child spans.

**Acceptance criteria:**
- [x] `service.name=agent-data-plane`
- [x] Decide and catalog HTTP + JDBC auto or manual spans
- [x] Decide outcome available as span attr (`outcome`) without high-cardinality candidate dumps

**Verification:**
- [x] `mvn test` in Data Plane passes
- [x] TraceQL or Grafana: spans for decide under the same trace id as AFD

**Dependencies:** Task O1, Task O4 (to verify parent link)

**Files likely touched:**
- `agent-data-plane/pom.xml`
- `agent-data-plane/src/main/java/**`
- `docs/run/compose/docker-compose.yml`

**Estimated scope:** Medium

---

## Task O6: Registry OTel + capability/manifest GET + JDBC

**Description:** Instrument Registry so hydrate-time GETs appear on the AR (and thus AFD) trace.

**Acceptance criteria:**
- [x] `service.name=agent-capability-registry`
- [x] Manifest/capability GET + JDBC spans
- [x] 404/controlled errors recorded as span status without logging secret headers

**Verification:**
- [x] `mvn test` in Registry passes
- [x] Hydrate path shows Registry spans in Tempo

**Dependencies:** Task O1; verify with Task O7

**Files likely touched:**
- `agent-capability-registry/pom.xml`
- `agent-capability-registry/src/main/java/**`
- `docs/run/compose/docker-compose.yml`

**Estimated scope:** Medium

---

## Task O7: Runtime OTel + hydrate + loop spans

**Description:** Instrument FastAPI Runtime with OTel; auto HTTP/httpx/SQLAlchemy; manual spans for `hydrate` and stub graph invoke; attach `correlation_id` after mint.

**Acceptance criteria:**
- [x] `service.name=agent-runtime`
- [x] `POST /v1/runs` continues inbound `traceparent` from AFD
- [x] Spans: `hydrate`, catalogue/registry client calls, `graph.invoke` (or stub loop)
- [x] Logs after start include `correlation_id`

**Verification:**
- [x] `uv run pytest` in Runtime passes
- [x] One jobs or chat start: Tempo shows AFD → AR → ADP/ACR children; `correlation_id` on AR span attrs

**Dependencies:** Task O1, Task O4

**Files likely touched:**
- `agent-runtime/pyproject.toml`
- `agent-runtime/app/main.py`
- `agent-runtime/app/hydrate.py`
- `agent-runtime/app/loop.py`
- `agent-runtime/app/runs.py`
- `agent-runtime/Dockerfile` (entrypoint order if SDK must preload)

**Estimated scope:** Medium

---

## Task O8: Control Plane OTLP (optional)

**Description:** Add lightweight OTLP traces/metrics for Control Plane catalogue `fetch` calls so ops browsing is not invisible. Defer if Phase 1 checkpoint is blocked.

**Acceptance criteria:**
- [x] `service.name=agent-control-plane`
- [x] Outbound fetches to ADP/ACR show in Tempo when UI is used
- [x] Does not block O9 if skipped (mark cancelled in this file)

**Verification:**
- [x] Open Control Plane UI; Tempo shows CP spans or task marked cancelled with reason

**Dependencies:** Task O1

**Files likely touched:**
- `agent-control-plane/package.json`
- `agent-control-plane/src/**`
- `docs/run/compose/docker-compose.yml`

**Estimated scope:** Small

---

## Checkpoint: Layer ②

- [x] Unbroken Tempo path for `fee_explain` (jobs or chat): AFD → ADP → AR → ACR
- [x] RED/latency for decide and runs queryable in Prometheus
- [x] Spot-check: no PII/secrets in span attributes
- [ ] Human review before business-event work

---

## Task O9: Emit journey business events on AFD / ADP / AR

**Description:** Emit allowlisted structured business events for the `fee_explain` journey so Layer ① drop-off is visible in Loki (and later KPIs).

**Acceptance criteria:**
- [x] Events exist with stable names: `chat.turn.received` (or `job.entitle.accepted`), `intent.decide.routed` | `intent.decide.clarified` | `intent.decide.abstained`, `chat.run.accepted` / `job.run.accepted`, `run.hydrate.succeeded` | `run.hydrate.failed`, `run.completed` | `run.failed`, and delivery/status poll success where applicable
- [x] Fields include `journey_id`, `session_id` and/or `correlation_id`, `route_id`/`route_version` when known, `outcome` — never full message body or claims
- [x] Jobs path uses the same event family with `ingress`/`channel` distinguishing job vs chat

**Verification:**
- [x] Demo turn: Loki query finds the sequence by `session_id` or `correlation_id`
- [x] Unit tests where emission is behind a small helper (preferred)

**Dependencies:** Task O2, Task O7 (for hydrate/complete)

**Files likely touched:**
- `agent-front-door/.../AssistantService.java`, `JobsService.java`
- `agent-data-plane/.../DecideService.java`
- `agent-runtime/app/runs.py`, `hydrate.py`, `loop.py`

**Estimated scope:** Medium

---

## Task O10: Journey KPI counters for fee_explain

**Description:** Low-cardinality counters (or OTel metrics) for journey outcomes so Grafana can chart route/clarify/abstain/complete/hydrate_fail rates.

**Acceptance criteria:**
- [x] Metrics exist for decide outcomes and run terminal states with labels from a fixed set (`journey_id`, `outcome`, `channel` / `ingress`)
- [x] No unbounded labels
- [x] Document PromQL examples in README or task notes

**Verification:**
- [x] After N demo turns, Prometheus shows non-zero series for at least routed + completed
- [x] Clarify/abstain paths increment when exercised

**Dependencies:** Task O9, Phase 1 OTel metrics path (O4–O7)

**Files likely touched:**
- Same services as O9; metric registration near event emission

**Estimated scope:** Medium

---

## Task O11: Grafana journey row for fee_explain

**Description:** Add a minimal Grafana dashboard (provisioned JSON under `docs/run/` or documented Explore queries) answering: outcome mix, completion rate, decide/run latency.

**Acceptance criteria:**
- [x] Dashboard or README “Explore” recipes cover the four on-call questions for `fee_explain`
- [x] Default time range suitable for local demos (e.g. last 15m–1h)
- [x] No orphan panels unrelated to the journey

**Verification:**
- [x] Manual: after demo traffic, panels/queries show data without editing PromQL from scratch

**Dependencies:** Task O10

**Files likely touched:**
- `docs/run/grafana/` (if provisioning) or `README.md`
- Possibly `docs/run/compose/docker-compose.yml` volume mounts for provisioning

**Estimated scope:** Small

---

## Checkpoint: Layer ①

- [x] Event sequence + KPI counters visible for `fee_explain`
- [x] Journey dashboard/recipes usable by a new session

---

## Task O12: DB pool metrics with service identity

**Description:** Export Hikari (Java) and SQLAlchemy/pool (Runtime) metrics so saturation ties to `service.name` already on OTel resources.

**Acceptance criteria:**
- [x] Active/idle/pending (or equivalent) pool metrics for AFD, ADP, ACR, AR
- [x] Series joinable to the same service names used in Tempo

**Verification:**
- [x] Prometheus query shows pool metrics per service after traffic
- [x] Manual: document which query to use when decide latency rises

**Dependencies:** Task O4–O7

**Files likely touched:**
- Java `application.yml` / datasource Micrometer binding
- `agent-runtime` engine/pool config + OTel metrics

**Estimated scope:** Medium

---

## Task O13: Compose resource labels + optional Postgres exporter

**Description:** Label containers/DBs by owning service; optionally add Postgres exporter or cAdvisor for local Layer ③ practice. Keep optional pieces clearly marked so Compose stays bootable without them if skipped.

**Acceptance criteria:**
- [x] Document mapping: `afd`→front-door, `adp`→data-plane, `ar`→runtime, `acr`→registry
- [x] Either (a) exporter/cAdvisor wired in Compose with service labels, or (b) task documents “app pool metrics only for local L3” and marks exporter deferred
- [x] No requirement for production k8s agents in this task

**Verification:**
- [x] Manual: README Layer ③ section matches what Compose actually runs

**Dependencies:** Task O12 for “app-only” path; none for docs-only deferral

**Files likely touched:**
- `docs/run/compose/docker-compose.yml`
- `README.md` or `docs/tasks/observability-plan.md` note

**Estimated scope:** Small

---

## Checkpoint: Layer ③

- [x] Pool (and optional infra) signals bound to service identity
- [x] Can narrate KPI → span → pool for a forced slow/fail scenario

---

## Task O14: Symptom alerts + short runbooks

**Description:** Define a minimal set of symptom-based alerts (thresholds suitable for local demo or as Grafana alert JSON) with three-line runbooks: meaning, first query, escalation stub.

**Acceptance criteria:**
- [x] Alerts cover: decide 5xx/error rate, hydrate failure rate, journey completion drop — not raw CPU pages
- [x] Each alert links to a runbook snippet in the README
- [x] Two severities only if alerting is enabled locally; otherwise document “ticket vs page” intent for when a real Alertmanager exists

**Verification:**
- [x] Manual: lower threshold once or use Explore to prove the query; runbook steps work

**Dependencies:** Task O10, Task O11

**Files likely touched:**
- Grafana alert provisioning or README

**Estimated scope:** Small

---

## Task O15: README / handbook observability notes

**Description:** Document how to verify the three layers locally: OTLP endpoints, example TraceQL/LogQL/PromQL, journey dashboard location, and what is still stubbed.

**Acceptance criteria:**
- [x] Root README Observability section updated (env is live; services export; how to Explore)
- [x] Pointer from this task list / plan to the README recipes
- [x] Explicit: no utterance/PII in telemetry

**Verification:**
- [x] Manual: a new session can follow README from compose up → see a trace without this chat

**Dependencies:** Task O11

**Files likely touched:**
- `README.md`
- Optionally per-service README if handbooks exist

**Estimated scope:** Small

---

## Task O16: Verification checklist (force hydrate fail)

**Description:** Add a short script or markdown checklist that forces a hydrate failure (or uses a known bad pin in a test harness) and confirms the failure is findable via Loki event + Tempo span + metric bump without reading source.

**Acceptance criteria:**
- [x] Checklist or script steps are reproducible on clean compose
- [x] Confirms: business event `run.hydrate.failed` (or equivalent), error span, KPI counter
- [x] Confirms redaction: no secrets in that telemetry

**Verification:**
- [x] Run the checklist once; all boxes pass
- [ ] Human sign-off

**Dependencies:** Task O9, Task O10, Task O7

**Files likely touched:**
- `README.md` (See a journey / force hydrate fail)
- Possibly a test-only fixture

**Estimated scope:** Small

---

## Checkpoint: Complete

- [x] O1–O7, O9–O16 done (O8 done or cancelled)
- [x] L3 narrative works for `fee_explain` in Grafana
- [x] Out of scope still out (L5, all journeys, production retention)
- [ ] Human approves before starting Phase 0 implementation in a build session
