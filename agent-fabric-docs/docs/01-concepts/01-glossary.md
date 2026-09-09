---
title: Glossary
sidebar_label: Glossary
description: "Every term of art in the Fabric, with a one-line definition and a link to the page that explains it properly."
---

# Glossary

One line each. Follow the link when one line is not enough.

Two distinctions cause most of the confusion here, so they are worth stating up front:

- **Catalogue-only versus executed.** The catalogue can record more than Agent Runtime does. Where a term is recorded but not acted on, it says so. The full list is [coverage status](/catalogue/coverage-status).
- **Audit versus observability.** Both watch a run. [Audit](/concepts/authoring-a-product/audit) is the evidence path — append-only, queried by `correlation_id`, kept. [Observability](/concepts/authoring-a-product/observability) is the ops path — OpenTelemetry into Grafana, for debugging.

## Boxes and services

| Term | Definition |
| --- | --- |
| **Enterprise Agent Fabric** | The shared front door and control plane for acting AI. Identity, routing, policy, and proof run once; domains keep the intelligence |
| **AFD** — Agent Front Door | The only public ingress. Entitles, freezes, and starts Runtime. Chat and jobs, `:3005` |
| **ADP** — Agent Data Plane | Catalogue and classify. Owns `POST /v1/intent/decide`. Does not pin or start Runtime. `:3007` |
| **ACP** — Agent Control Plane | The catalogue browser UI. No database, no decide API. Not a Fabric box. `:3006` |
| **AR** — Agent Runtime | Pins the freeze, hydrates, and runs the LangGraph graph. `:3008` |
| **ACR** — Agent Capability Registry | Published capabilities and manifests as immutable `id@version`. Hydrated once, at pin. `:3009` |
| **AADP** — Agent Audit Data Plane | Append-only evidence ingest and query. `:3012` |
| **AACP** — Agent Audit Control Plane | Ops UI over evidence chains. No database of its own. `:3013` |
| **Agent Plane** | ACP plus ADP, one per trust domain. Classifies; does not execute |
| **Shared** | Memory, RAG, model, and tools — called *from* Runtime, not built into it. Largely not implemented |
| **PEP** — Policy Enforcement Point | The dual user-and-agent check before a tool invoke. Production target, not local |
| **BFF** | The connection-bound shape of the Chat Front Door fleet, as opposed to the handler-shaped API fleet |
| **DMS** | The enterprise document store. Front Door puts bytes there and starts Runtime with a JSON id only |
| **agent-mocks** | Local HTTP doubles for domain tools and corpus gateways. `:3010` |

## Catalogue objects

| Term | Definition |
| --- | --- |
| **[Route](/concepts/authoring-a-product/route)** | The product. A versioned row keyed `(route_id, route_version)`; one version per id is `active` |
| **[Capability](/concepts/authoring-a-product/capability)** | An immutable published `id@version`. Either `kind=domain` (HTTP to a business API) or `kind=agent` (starts a child route) |
| **Manifest** | The list of capability references a route pins. Stored on the route as `tool_manifest` plus `tool_manifest_version` |
| **[Prompt pack](/concepts/authoring-a-product/prompts)** | The text the LLM sees: a `host` string plus a template per `llm_role` |
| **Workflow** | A fixed, ordered stage list. Required by autonomy modes 2 and 3 |
| **Stage** | One named step in a workflow: an id, an optional tool, an `llm_role`, optionally `branch` or `human_gate` |
| **[Corpus](/concepts/authoring-a-product/corpus)** | A registered search gateway — a URL and collection that prefetch POSTs to |
| **[Memory profile](/concepts/authoring-a-product/memory)** | Route policy for `conversation`, `working`, `loop`, and `long_term`. Policy, not a store |
| **[Retrieval](/concepts/authoring-a-product/retrieval)** | Route-level corpus policy: a `mode` plus a `scope` of corpus ids |
| **`active`** | The one version of a route that new requests classify against. Implies `status='active'` |
| **`published`** | An immutable released cut. Not necessarily the live one |
| **`draft` / `retired`** | Work in progress, not hydratable / withdrawn from service |

## Execution

| Term | Definition |
| --- | --- |
| **Entitle** | Check the caller's claims and channel against the route. Jobs skip classify, never entitle |
| **Decide** | The Data Plane classify call. Returns `route`, `clarify`, or `abstain` |
| **`clarify`** | Decide asked the user to choose between candidates. Never pins |
| **`abstain`** | Decide declined to route. Never pins |
| **Freeze** | The Front Door record mapping `session_id` to a pinned route and correlation id. Route stickiness with a TTL — **not** conversation memory |
| **Pin** | The durable Runtime record of `route_id` plus `route_version`. Fixes the catalogue snapshot the run executes against |
| **[Hydrate](/concepts/executing-a-request/request-lifecycle)** | One-time resolution of the pinned route, manifest, capabilities, and prompt onto the run, before the first LLM call |
| **[`goal`](/concepts/executing-a-request/run-data)** | The immutable ingress payload: a job `payload` or a chat utterance. Never updated mid-run |
| **`slots`** | Structured JSON per completed stage, at `working.slots[stage_id]` |
| **`notes`** | Append-only strings on `working`, fed to LLM stages |
| **`GraphState`** | The Runtime state object: `result`, `goal`, `notes`, `slots` |
| **`activation_target`** | Where Runtime runs for this route. Channels never dial it directly |
| **`agent_client_id`** | The software identity pinned on the run, distinct from the user |
| **`human_gate`** | A workflow stage that pauses the run at `waiting` until a person resumes it through `/turns` |
| **Escalation** | A Mode 1 tool that files an async ticket and lets the parent run **complete**. Not a gate |
| **Evidence chain** | Every audit event sharing one `correlation_id`, time-ordered. A logical chain, not a hash chain |

## Identifiers

Who mints what, and what it is good for. Detail: [identifiers](/concepts/executing-a-request/identifiers).

| Term | Definition |
| --- | --- |
| **`request_id`** | One HTTP hop. Front Door mints it or echoes `X-Request-Id` |
| **`session_id`** | One journey instance: `chat-…`, `job-…`, or `sub-…`. The freeze key |
| **`correlation_id`** | One run. **Runtime alone mints it.** The status-poll handle and the audit chain key |
| **`idempotency_key`** | Caller-supplied jobs dedup key. The same key returns the original `correlation_id` |
| **`decision_id`** | An audit join id minted at decide. Not yet carried onto the freeze event |
| **`journey_id`** | A KPI bucket, `chat.{route_id}` or `job.{route_id}`. Not unique per request |
| **`trace_id`** | The W3C OpenTelemetry trace. Links spans in Tempo, unrelated to the audit store |
| **`event_id`** | The audit row key. Makes ingest idempotent |
| **`parent_correlation_id`** | Links a `kind=agent` child run back to its parent |

## Autonomy

| Term | Definition |
| --- | --- |
| **[`autonomy_mode`](/concepts/executing-a-request/autonomy-modes)** | The integer `0`–`3` on the route. Answers exactly one question: who picks the next step |
| **[Mode 0 — Single inference](/autonomy/mode-0-single-inference)** | Nobody picks. One LLM call from a prompt pack. No tools |
| **[Mode 1 — Autonomous](/autonomy/mode-1-autonomous)** | The LLM picks, from the hydrated manifest, bounded by `max_loop_steps` |
| **[Mode 2 — Deterministic](/autonomy/mode-2-deterministic)** | The workflow designer picks. A fixed stage list |
| **[Mode 3 — Guided](/autonomy/mode-3-guided)** | The designer fixes the outer stages; the LLM picks tools inside a stage allowlist |
| **[`llm_role`](/concepts/authoring-a-product/llm)** | How a stage executes: `none`, `classify`, `synthesis`, or `query_formulation` |
| **`max_loop_steps`** | The Mode 1 iteration budget. Defaults to `8`. Exceeding it fails the run |
| **Allowlist** | The Mode 3 per-stage list of permitted capabilities. Catalogue-only today |
| **`CALL` / `ASK` / `DONE`** | The Mode 1 loop verbs. The live path uses a structured `AgentDecision` with the same three actions |

## Governance and cross-cutting

| Term | Definition |
| --- | --- |
| **Three principals** | The user who asked, the agent acting as software, and the Runtime workload. Never conflated |
| **FR-5** | The rule that chat and UI responses must not leak `route_id`, `run_id`, confidence, or router internals |
| **`router_layer`** | Which decide layer matched: `rules`, `retrieve`, or `llm`. Server-side only |
| **`deterministic_prefetch`** | The retrieval mode where the app packs corpora *before* generate. The model cannot skip it |
| **`working`** | Session-scoped scratch, `{notes, slots}`, on the run pin. Honoured by Runtime |
| **`loop=checkpoint`** | A crash cursor allowing a failed run to resume from `resume_index`. Honoured by Runtime |
| **`conversation=session`** | Policy saying the next turn should see prior utterances. **Catalogue-only** — there is no transcript store |
| **`long_term=retrieve_only`** | Policy for facts recalled in a later journey. **Catalogue-only** — Shared Memory is not built |
| **Business events** | Allowlisted journey breadcrumbs on the ops path. Not the audit store |
