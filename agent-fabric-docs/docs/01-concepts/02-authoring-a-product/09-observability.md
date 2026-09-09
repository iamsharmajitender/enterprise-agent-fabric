---
title: Observability
sidebar_label: Observability
description: "What the fabric emits about your route without being asked, which parts of it your authoring choices shape, and where the runbook lives."
---

# Observability

Like [audit](/concepts/authoring-a-product/audit), observability is platform-level: there is no route field that configures it. Unlike audit, what you author changes the *shape* of what you get quite a lot, because the breadcrumbs are keyed to your route id and emitted per stage.

This page is about that connection — what your authoring choices do to the telemetry. The operational runbook (starting the LGTM stack, following a journey, example queries) lives in the [repository README](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/README.md#observability-grafana-lgtm) and is not repeated here.

## What you get automatically

Every box exports OpenTelemetry over OTLP to a local `otel-lgtm` container — Grafana on `:3000`, OTLP on `:4317` and `:4318`. Traces land in Tempo, metrics in Prometheus, logs in Loki.

| Box | Traces | Metrics | Logs |
| --- | --- | --- | --- |
| Agent Front Door | Yes | Yes | Yes |
| Agent Data Plane | Yes | Yes | Yes |
| Agent Capability Registry | Yes | Yes | Yes |
| Agent Runtime | Yes | Yes | Yes |
| Agent Audit Data Plane | Yes | Yes | **No** |
| Agent Control Plane | Yes | No | No |

Sampling is `1.0` locally. Runtime adds FastAPI, httpx, and SQLAlchemy auto-instrumentation, so a stage's outbound HTTP call is a child span without anyone writing tracing code.

## What your route becomes

This is the part authoring controls.

| You author | Telemetry effect |
| --- | --- |
| `route_id` | Becomes the **`journey_id`** bucket: `chat.{route_id}` or `job.{route_id}`. This is the label on `fabric_journey_outcome_total`, so your route id is the unit of KPI reporting |
| Workflow stage ids | Become `stage_id` on every `run.stage.*` event. Vague stage names produce vague dashboards |
| Stage `llm_role` | Decides whether a stage emits `run.llm.*` at all, and appears as a field on the event |
| `autonomy_mode` | Determines the graph shape, and therefore how many stage events one run emits |
| Capability `output_schema` | Appears as `llm_schema` and `llm_structured` on the LLM events |

Choosing a stage id is a naming decision that outlives the code. Pick names a person reading a Grafana panel at 2am will recognise.

## Business events

Business events are log lines whose body is the event name, with fields carried as structured attributes. They are the journey-level breadcrumbs, distinct from spans.

| Box | Events |
| --- | --- |
| Front Door — chat | `chat.turn.received`, `chat.run.started`, `chat.run.delivered` |
| Front Door — jobs | `job.entitlement.accepted`, `job.entitlement.rejected`, `job.run.started`, `job.run.delivered` |
| Data Plane | `chat.intent.routed` / `.clarified` / `.abstained`, and the `job.intent.*` equivalents |
| Runtime — run | `run.hydrate.succeeded` / `.failed`, `run.graph.started` / `.completed` / `.waiting` / `.failed` |
| Runtime — stage | `run.stage.started` / `.completed` / `.failed` |
| Runtime — LLM | `run.llm.started` / `.completed` / `.failed` |

The Capability Registry, Audit, and Control Plane emit no business events.

The LLM events carry `llm_model`, `llm_role`, `llm_schema`, `llm_structured`, latency, and request/response digests. They are the fastest way to answer "did the model actually get the prompt I think it got" without turning on payload logging.

:::note Not in the README table
The `run.llm.*` family is implemented but missing from the business-events table in the repository README. It is listed above.
:::

## Correlation

| Identifier | Minted by | Where it appears |
| --- | --- | --- |
| `request_id` | Front Door, echoing `X-Request-Id` if present | Span attribute and MDC, forwarded on outbound calls |
| `correlation_id` | **Runtime only** | Run span, every run event, and the audit chain key |
| `session_id` | Front Door | Spans and business events |
| `journey_id` | Derived from `route_id` | Business events and the outcome counter |
| `trace_id` / `span_id` | OpenTelemetry | Attached to JSON log lines |

W3C `traceparent` propagates across boxes, so one Tempo trace spans the whole request. Full detail: [identifiers](/concepts/executing-a-request/identifiers).

**Deliberately excluded** from metrics and spans: utterance text, tokens, and stub claims. Content is represented by digests.

## Payload logging

`FABRIC_LOG_STAGE_PAYLOADS` adds raw request and response JSON to the stage and LLM events. It is a debugging aid, and it defeats the privacy rule above.

:::caution Compose and the README disagree
Compose sets it to `1`. The README documents the default as `0`. Local runs are therefore logging raw stage payloads unless you override it — fine for a laptop, wrong for anything shared.
:::

## Gaps worth knowing

- **No Grafana dashboards are checked in.** The example PromQL, TraceQL, and LogQL live in the README as text.
- **Service names differ from the README.** Compose sets `agent-front-door`, `agent-data-plane`, `agent-runtime-shared` / `-custom`; the README lists longer `agent-fabric-*` names. Use the label browser rather than the README when writing a query.
- **No per-route observability configuration exists**, and none is planned. If you need a route-specific signal, express it through stage naming and the outcome counter.
