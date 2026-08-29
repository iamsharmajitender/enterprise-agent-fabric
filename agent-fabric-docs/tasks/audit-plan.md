# Implementation Plan: Agent audit (fabric evidence chain)

## Overview

Add a **fabric evidence chain** so ops and risk can answer: why this route, under what entitlement snapshot, which frozen contract ran, what each stage saw/wrote, and how the run ended.

v1 deferred decision audit (no `/v1/decisions`, no audit table on ADP — [todo.md](./todo.md) Task 15). Freeze + `correlation_id` + OTel help operations; they are **not** an append-only, queryable exam trail with retention and redaction.

**Two new boxes** (not folded into ACP catalogue UI or into `adp` / `ar` databases):

| Box | Port | Stack | Job |
| --- | --- | --- | --- |
| **agent-audit-data-plane** (AADP) | **3012** | Java 21 hexagonal + Flyway + Postgres DB `audit` | Ingest append-only events; query APIs |
| **agent-audit-control-plane** (AACP) | **3013** | TypeScript UI/client (like ACP); **no database** | Ops UI; **only** calls AADP over HTTP |

> **Ports:** Compose already binds **3010** to `agent-mocks`, so audit uses **3012** / **3013**.

Producers **AFD, ADP, AR, ACR** send events to AADP. They **never** call AACP. Channel/chat JSON stays slim (FR-5); evidence is a separate audience.

**Task list:** [audit-todo.md](./audit-todo.md). **Docs map:** [README.md](../README.md). **Parked summary:** [future-enhancement.md](./future-enhancement.md#3-audit--decision-record--evidence-chain).

**Not in this plan:** IdP / PEP / policy dual-check; Shared Memory (`conversation` / `long_term`); model router; hydrate-fidelity / dual-store publish lint; implementing Kafka in the first cut (envelope designed for it); putting audit tables on `adp` or `ar`; showing `router_layer` on chat wire JSON.

Observability (OTel → LGTM) remains the **ops** path — [observability-plan.md](./observability-plan.md). Audit is the **evidence** path. Same `correlation_id` / `session_id` may link them; they are not the same store.

---

## Present vs remaining

| Evidence | v1 today | This plan |
| --- | --- | --- |
| Decide outcome / candidates / layer | In-process + OTel; not durable audit | Phase A: ADP → AADP `decide.*` |
| Freeze / pin (`route_id@version`, keys) | AFD freeze store (TTL); not exam trail | Phase A: AFD → AADP `freeze.*` / `pin.*` |
| Hydrate snapshot (caps @ version, invoke/schema digests) | AR pin internals; not query product | Phase A: AR → AADP `hydrate.snapshot` |
| Run terminal (completed / failed / waiting) | AR status + AFD poll | Phase A: AR → AADP `run.terminal` |
| Stage I/O digests | Logs / spans only | Phase B: AR → AADP `stage.*` |
| Capability / manifest publish provenance | ACR DB only | Phase B: ACR → AADP `*.published` |
| Ops browse by `correlation_id` | Grafana / manual | Phase A: AACP → AADP query APIs |
| Kafka durability | Stub / not audit | Later: same envelope on bus (parked in todo) |

---

## Architecture decisions (accepted)

### Boxes and boundaries

1. **AADP owns durability.** Append-only events in Postgres `audit`. Producers POST events; AACP and other ops clients GET chains.
2. **AACP is UI-only.** No Fabric DB. Pattern matches catalogue ACP → ADP: workload header (e.g. `X-Workload: aacp`), query only.
3. **Producers never call AACP.** AFD / ADP / AR / ACR → AADP only.
4. **Separate store properties (why not OTel-only):**

| Property | Meaning |
| --- | --- |
| **Append-only** | Insert events; no rewrite of history (redact via policy/tombstone, not silent UPDATE of past facts). |
| **Queryable** | APIs by `correlation_id`, `session_id`, time range — not “grep Loki and hope.” |
| **Retention** | Policy TTL/archive (run-pin TTL ≠ audit retention). |
| **Redaction** | Allowlisted payload: hashes/digests by default; no raw utterance, claims JSON, bearer tokens, or secrets. |

### Transport

5. **First cut: async non-blocking HTTP** to `POST /v1/audit/events` on AADP. Decide / freeze / `202` start **must not wait** on audit commit (matches Agent Plane packs: audit lag is OK).
6. **Failure mode:** bounded in-process queue / fire-and-forget client; metric on drop or non-2xx; accept local gaps until Kafka/outbox.
7. **Later: Kafka** (or bus) carries the **same envelope**; AADP consumes. HTTP remains for backfill/replay and local Compose. Outbox in producers if “almost no loss” is required — parked, not Phase A/B blockers.

### Phases

8. **Phase A** (ship first): `decide.*`, `freeze.*` / `pin.*`, `hydrate.snapshot`, `run.terminal` + AACP lookup by `correlation_id`.
9. **Phase B** (same track, next): `stage.*` digests + ACR `capability.published` / `manifest.published`; AACP timeline includes stages; document retention/redaction defaults.

### Correlation

10. Reuse existing ids: W3C `traceparent` (ops), AR `correlation_id`, AFD `session_id` / jobs idempotency key. Optional `decision_id` minted at decide emit time for decide→pin join when `correlation_id` does not exist yet.

---

## Event envelope

Stable fields for HTTP now and Kafka later:

| Field | Role |
| --- | --- |
| `event_id` | UUID; idempotent insert key (duplicate POST → same row / 200) |
| `event_type` | e.g. `decide.completed`, `freeze.written`, `pin.started`, `hydrate.snapshot`, `stage.completed`, `run.terminal`, `capability.published` |
| `occurred_at` | Producer clock (ISO-8601) |
| `producer` | `afd` \| `adp` \| `ar` \| `acr` |
| `correlation_id` | Run key when known (nullable on early decide) |
| `session_id` | Chat session (`chat-{uuid}`) or jobs/sub freeze key (`job-{uuid}` / `sub-{uuid}`) when known |
| `decision_id` | Optional join from decide → freeze |
| `payload` | Allowlisted JSON per `event_type` (hashes/digests; see below) |

### Phase A payload gist

| `event_type` | Producer | Payload gist |
| --- | --- | --- |
| `decide.completed` (or `.clarify` / `.abstain`) | ADP | `outcome`, `route_id` / `route_version` when route, `candidates` (ids only), `router_layer`, `claims_hash`, `utterance_hash`, `channel`, `ingress` |
| `freeze.written` / `pin.started` | AFD | freeze key, `route_id@version`, `correlation_id`, `ingress` (chat/jobs) |
| `hydrate.snapshot` | AR | list of `capability_id@version`, invoke URL **digest** (or allowlisted host path), input/output schema digests, `manifest_id@version`, `route_id@version` |
| `run.terminal` | AR | `status` (`completed` / `failed` / `waiting`), reason codes, `route_id@version` |

### Phase B payload gist

| `event_type` | Producer | Payload gist |
| --- | --- | --- |
| `stage.started` / `stage.completed` / `stage.failed` | AR | `stage_id`, `llm_role` or tool id, request/response **digests**, latency_ms, status (optional redacted allowlist fields later) |
| `capability.published` / `manifest.published` | ACR | `id`, `version`, publisher workload, content digest |

**Default deny:** raw utterance text, full claims JSON, `Authorization`, tool bodies with PII, LLM prompts/completions.

---

## AADP APIs (sketch)

| Method | Path | Role |
| --- | --- | --- |
| `POST` | `/v1/audit/events` | Append one event (idempotent on `event_id`) |
| `GET` | `/v1/audit/chains/{correlation_id}` | Ordered events for a run |
| `GET` | `/v1/audit/sessions/{session_id}` | Events for a session / job freeze key |
| `GET` | `/v1/audit/events` | Filter: time range, `event_type`, `route_id` (bounded) |

Health unauthenticated; ingest/query require stub workload or future IdP (local: `X-Workload` + stub claims pattern consistent with fabric).

---

## AACP (sketch)

- Local UI on **3011**: search by `correlation_id` / `session_id`; render Phase A chain; Phase B adds stage timeline.
- Env: `AUDIT_DATA_PLANE_URL=http://agent-audit-data-plane:3010` (host: `localhost:3010`).
- No decide, no catalogue mutate, no start Runtime.

---

## Demo path (definition of done for the track)

```text
./agent-fabric-scripts/stack/start-app.sh   # includes AADP :3010, AACP :3011, DB audit
# fee_explain chat or jobs
# AACP: paste correlation_id → see decide → freeze/pin → hydrate → terminal
# Phase B: same page shows stage.* rows; ACR publish visible for a seed cut
# Kill AADP: decide/start still succeed; metric shows audit drop (async fail-open)
```

---

## Suggested order

1. Foundation (envelope, DB `audit`, scaffolds, Compose ports)
2. Phase A — AADP ingest + query
3. Phase A — producer async clients (ADP, AFD, AR)
4. Phase A — AACP lookup UI
5. Phase B — stage digests + ACR publish + AACP timeline
6. Later — Kafka consumer + optional outbox ([audit-todo](./audit-todo.md) parked tasks)

---

## Out of scope (do not reopen here)

- Merging audit into existing ACP (catalogue) process or ADP schema
- Blocking decide/start on audit 2xx
- Full SIEM / legal-hold product UI
- Shared Memory transcripts as audit events
- Hydrate silent-drop fixes (platform hardening §1)
- Dual ADP/ACR publish lint (hardening §2)
