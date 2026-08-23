# Implementation Plan: Three-layer observability (local Fabric)

## Overview

Instrument the running Agent Fabric so a single chat (or jobs) turn is visible end-to-end in the existing Grafana LGTM stack: **Layer ① business** journey events and KPIs for `fee_explain`, **Layer ② service** golden signals and unbroken OTel traces across AFD → ADP → AR → ACR, **Layer ③ infrastructure** resource signals labeled by owning service. Collection platform already exists (`otel-lgtm`); apps do not export yet. Target maturity: **L3 on the tier-1 journey** ([Observability blueprint](https://jitendersharma.dev/blueprints/observability-blueprint)).

**Not in this plan:** L4/L5 predictive/autonomous ops, production retention tiers, real Kafka event bus, decision-audit store, second AFD fleet.

**Docs map:** [docs/README.md](../README.md). **Behaviour / architecture source:** [README Observability section](../../README.md), [enterprise-agent-fabric architecture](../04-architecture/README.md). Do not reopen locked fabric rules.

## Architecture Decisions

- **Reuse LGTM, do not replace it.** Apps export OTLP HTTP to `otel-lgtm:4318` (host: `localhost:4318`). Grafana already has Prometheus, Loki, Tempo.
- **Three IDs, distinct jobs.** W3C `traceparent` = distributed trace. AR `correlation_id` (`corr-*`) = run/freeze/jobs key (span attr + logs after start). `session_id` = journey instance. Optional constant `journey_id=chat.fee_explain` (or `job.fee_explain`) for KPI grouping.
- **Java path:** Micrometer + OpenTelemetry exporter (or Spring Boot OTel starter) on Front Door, Data Plane, Registry — auto servlet / RestClient / JDBC; manual spans only for decide, runtime start, hydrate-adjacent work.
- **Python path:** OpenTelemetry SDK + FastAPI / httpx / SQLAlchemy instrumentors on Runtime; manual spans for `hydrate` and stub `graph.invoke`.
- **Control Plane:** lowest priority for the chat graph; still get `OTEL_*` when Phase 0 lands so catalogue ops are not a blind spot.
- **Business events are structured logs (and/or low-cardinality counters), not a new bus.** Stable event names; allowlisted fields; no utterance, claims JSON, or tokens.
- **Infra binding over orphan host graphs.** Service name on every resource; Hikari / SQLAlchemy pool metrics first; optional Postgres exporter / cAdvisor later.
- **Symptom alerts only** after Layer ①+② work; each alert needs a three-line runbook link.

## Correlation contract

| ID | Role | Rule |
| --- | --- | --- |
| `traceparent` / `tracestate` | Tempo glue | AFD accepts or generates; every RestClient / httpx outbound propagates |
| `correlation_id` | Run business key | Minted at AR start; on freeze, jobs responses, logs/spans after start |
| `session_id` | Journey instance | AFD mints; baggage or span attrs on decide + run |
| `journey_id` | KPI bucket | e.g. `chat.fee_explain` / `job.fee_explain` |

Metric labels stay bounded: `service`, `route` template, `status_class`, `outcome`, `route_id` (catalogue-sized set), `channel`. Never `session_id`, `correlation_id`, utterance, or user `sub` as metric labels.

## On-call questions (instrument only to answer these)

1. Did this turn **route**, **clarify**, or **abstain** — and why?
2. When `fee_explain` fails, is it **decide**, **hydrate**, **loop**, or **delivery**?
3. Is ADP or ACR slower than usual on the pin path?
4. Is Postgres / pool saturation bound to the failing service?

## Demo path (definition of done for this plan)

```text
./docs/run/scripts/start-app.sh
# fee_explain chat or jobs demo
# Grafana :3000 → Tempo: one trace AFD → ADP → AR → ACR
# Loki: business events by session_id / correlation_id
# Prometheus: decide outcome rates + HTTP RED
```

Forced hydrate failure is diagnosable from telemetry alone (no source reading).

## Task List

### Phase 0: Foundation (Compose + edge identity)

- [ ] Task O1: OTEL env + depends on `otel-lgtm` for all app services
- [ ] Task O2: Structured JSON logging baseline (Java + Python)
- [ ] Task O3: AFD request ID / `traceparent` accept-or-mint at channel edge

### Checkpoint: Foundation

- [ ] Compose up; services start with `OTEL_*` set
- [ ] At least one service exports a health-related signal visible in Grafana Explore (or documented “waiting on Phase 1 SDK”)
- [ ] Review before Java/Python SDK work

### Phase 1: Layer ② — traces + RED on the chat/jobs path

- [ ] Task O4: Front Door OTel + RestClient propagation (decide, catalogue, runtime)
- [ ] Task O5: Data Plane OTel + decide / catalog / JDBC
- [ ] Task O6: Registry OTel + capability/manifest GET + JDBC
- [ ] Task O7: Runtime OTel + FastAPI / httpx / SQLAlchemy + hydrate + loop spans
- [ ] Task O8: Control Plane OTLP (catalogue client fetches) — optional if time-boxed after O4–O7

### Checkpoint: Layer ②

- [ ] One `fee_explain` turn: unbroken Tempo trace across AFD → ADP → AR → ACR
- [ ] RED histograms queryable for decide and `/v1/runs`
- [ ] No PII/secrets in span attributes (spot-check)

### Phase 2: Layer ① — business journey for `fee_explain`

- [ ] Task O9: Emit journey business events on AFD / ADP / AR
- [ ] Task O10: Journey KPI counters (route / clarify / abstain / complete / hydrate_fail)
- [ ] Task O11: Grafana journey row (or provisioned dashboard JSON) for `fee_explain`

### Checkpoint: Layer ①

- [ ] Demo utterance produces the event sequence in Loki
- [ ] PromQL (or dashboard) shows outcome mix for the journey

### Phase 3: Layer ③ — infra bound to service identity

- [ ] Task O12: Hikari + SQLAlchemy pool metrics with `service` resource attrs
- [ ] Task O13: Compose/resource labels + optional Postgres exporter or cAdvisor (local)

### Checkpoint: Layer ③

- [ ] Pool / DB signal for `agent-data-plane` (or `adp`) joinable to the same service name as traces

### Phase 4: Intelligence (L3 operating slice)

- [ ] Task O14: Symptom alerts + short runbooks (decide errors, hydrate fail, journey completion drop)
- [ ] Task O15: README / handbook notes — how to Explore traces, logs, journey KPIs
- [ ] Task O16: Verification script or doc checklist (force hydrate fail; find via telemetry)

### Checkpoint: Complete

- [ ] All acceptance criteria in [observability-todo.md](./observability-todo.md) met
- [ ] Maturity L3 on `fee_explain`: KPI → span → resource narrative works in a demo
- [ ] Human review before expanding journeys beyond `fee_explain`

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| High-cardinality metric labels | High | Allowlist labels; put ids only on logs/span attrs |
| Broken context across RestClient/httpx | High | Phase 1 checkpoint requires unbroken Tempo path |
| Logging utterance / stub claims | High | Allowlisted fields; security spot-check in O16 |
| Scope expands to all routes / L5 | Med | Journey locked to `fee_explain` until checkpoint |
| OTel deps slow local builds | Low | Prefer Boot starter / auto-instrumentation; keep export interval short only in Compose |

## Open Questions

- Prefer Spring Boot OpenTelemetry starter vs Micrometer OTLP registry only for the three Java services? (Default: Boot OTel starter if it stays Boot 3.5-compatible.)
- Ship Loki via OTLP logs vs Docker logging driver? (Default: OTLP logs from app SDKs where easy; otherwise JSON stdout + document Explore query.)
- Control Plane instrumentation: same Phase 1 milestone or defer to after chat-path RED is green? (Default: Task O8 after O4–O7.)
