---
title: Audit
sidebar_label: Audit
description: "The evidence chain: what every box emits, what the envelope allows, and why an author cannot configure any of it."
---

# Audit

Audit is **platform evidence, not a catalogue knob**. No route field turns it on, off, or sideways. What you author still shapes the evidence — your pins become the hydrate snapshot, your stages become the stage events — but you cannot opt out and you cannot add fields.

That is the point. Evidence you can switch off is not evidence.

Audit is also **not** [observability](/concepts/authoring-a-product/observability). Observability is the ops path: OpenTelemetry into Grafana, sampled, dropped freely, tuned for debugging. Audit is the evidence path: append-only Postgres, idempotent, queried by `correlation_id` months later. They share identifiers and nothing else.

## The envelope

Every event, from every producer, has the same shape.

| Field | Type | Notes |
| --- | --- | --- |
| `event_id` | UUID | Idempotent insert key. A duplicate is silently ignored |
| `event_type` | string | `decide.completed`, `freeze.written`, `hydrate.snapshot`, `stage.completed`, `run.terminal`, … |
| `occurred_at` | ISO-8601 | Producer clock |
| `producer` | `afd` \| `adp` \| `ar` \| `acr` | Which box emitted it |
| `correlation_id` | string \| null | The run key. Null on decide, which happens before a run exists |
| `session_id` | string \| null | `chat-…`, `job-…`, or `sub-…` |
| `decision_id` | string \| null | Intended decide → freeze join |
| `payload` | object | Allowlisted per event type |

The store adds `received_at` at insert.

**The payload is deny-listed at ingest.** `utterance`, `message`, `claims`, `authorization`, `prompt`, and `completion` are rejected. Content is represented by `sha256:` digests instead — `utterance_hash`, `claims_hash`, `request_digest`, `response_digest`. You can prove *that* a given input produced a given output without storing either.

## What each box emits

| Producer | Event | Payload highlights |
| --- | --- | --- |
| **Data Plane** | `decide.completed`, `decide.clarify`, `decide.abstain` | `outcome`, `route_id`, `route_version`, `candidates`, `router_layer`, `claims_hash`, `utterance_hash`, `channel`, `ingress` |
| **Front Door** | `freeze.written` | `route_id`, `route_version`, `ingress`, `freeze_key`, and `parent_correlation_id` on a subagent start |
| **Runtime** | `hydrate.snapshot` | The pinned `route_id@version`, manifest, prompt, retrieval block, and every capability with digests of its invoke URL and schemas |
| **Runtime** | `stage.completed` / `stage.failed` | `stage_id`, `llm_role`, `status`, `latency_ms`, request and response digests |
| **Runtime** | `run.terminal` | `status` (`completed`, `failed`, or `waiting`), route pin, `reason_code` |
| **Capability Registry** | `capability.published`, `manifest.published` | The published id, version, and a digest of the body |

The hydrate snapshot is the interesting one for an author. It records exactly which capability versions and which schema shapes were resolved at pin — so when someone asks in six months why a run behaved the way it did, the answer is in the row rather than in whatever the catalogue happens to say today.

:::caution Registry events fire on the API, not the seed
`capability.published` and `manifest.published` are emitted from the HTTP `PUT` handler. Loading capabilities through the seed SQL writes the rows without emitting anything.
:::

## Transport

Async fire-and-forget HTTP `POST` to `/v1/audit/events` on the Audit Data Plane, from a daemon thread pool. Decide, freeze, and start **do not wait** for a 2xx.

The failure mode is deliberate and worth knowing: if the audit plane is down, the emit logs a warning and the caller continues. **It fails open.** A request is never blocked by the evidence path, which also means a sustained audit outage silently loses events. There is no outbox and no Kafka transport — both are planned, neither is built. There is no drop metric either, so the only signal today is the warning in the producer's logs.

When `AUDIT_DATA_PLANE_URL` is unset the client is a no-op, which is how tests and bare local runs avoid the dependency.

## Storage

One table, `audit.events`, keyed by `event_id`, indexed on `(correlation_id, occurred_at, received_at)`, `(session_id, …)`, and `(event_type, occurred_at)`.

Append-only is enforced by convention and absence rather than by the database: no `UPDATE` or `DELETE` path exists in the application, and a duplicate `event_id` is caught and dropped.

:::note "Evidence chain" does not mean hash chain
A chain is **every event sharing a `correlation_id`, ordered by time**. The joins — `decision_id`, `session_id`, `parent_correlation_id` — are logical foreign keys, not cryptographic links. Nothing is Merkle-linked, and a row is not tamper-evident on its own.
:::

Retention is documented, not implemented. Local runs keep everything; production suggests 30–90 days. There is no garbage collection job.

## Reading a chain

| Endpoint | Returns |
| --- | --- |
| `GET /v1/audit/chains/{correlationId}` | Every event for one run, time-ordered |
| `GET /v1/audit/sessions/{sessionId}` | Every event for one session |
| `GET /v1/audit/workflows?limit&offset&status` | Completed or in-progress runs, including `parent_correlation_id` |

The Audit Control Plane on [:3013](http://localhost:3013) is the UI over those endpoints — it holds no database of its own. It lists completed and in-progress runs, toggles between a flat list and a nested view that groups `kind=agent` children under their parent, searches by `correlation_id` or `session_id`, and links each route back to the catalogue on the Control Plane.

A typical chain reads: `decide.completed` → `freeze.written` → `hydrate.snapshot` → `stage.completed` × n → `run.terminal`.

## Not built

Do not design against these.

| Gap | Status |
| --- | --- |
| `pin.started` event | Named in the plan and the service pack. Never emitted — `freeze.written` is the only Front Door event |
| `stage.started` audit event | Exists as an OpenTelemetry event only. Not in the evidence store |
| `decision_id` on `freeze.written` | Decide mints one; Front Door writes `null`. The decide → freeze join is not wired |
| `GET /v1/audit/events` with time and type filters | Sketched in the plan. Not implemented |
| Kafka transport, producer outbox | Planned |
| Audit drop metric | Planned. Only a log warning today |
| Scheduled retention | Documented policy only |

Full detail on the box: [Agent Audit service pack](/architecture/service-packs/agent-audit). Frozen event fixtures: [reference](/reference/).
