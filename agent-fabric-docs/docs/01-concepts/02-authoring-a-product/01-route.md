---
title: Route
sidebar_label: Route
description: "The route is the product. What the row holds, which fields each autonomy mode requires, how versions and active status work, and how decide picks one."
---

# Route

A route **is** the product. Everything else on this section — capability, prompts, schema, retrieval, memory, corpus — is a row that hangs off one. Authoring a product means writing a route row and the rows it points at.

Routes live in `dataplane.routes` on the Agent Data Plane. The primary key is **`(route_id, route_version)`**, so a route id is a family of immutable versions, not a single mutable record.

## What the row holds

| Field | What it does | Required |
| --- | --- | --- |
| `route_id` | Stable product identifier | Always |
| `route_version` | Immutable catalogue cut | Always |
| `intent_label` | The label decide returns on `outcome=route` | Always |
| `status` | `draft`, `published`, `active`, or `retired` | Always. Defaults to `published` |
| `active` | Marks the one live version per `route_id` | Always. Defaults to `false` |
| `autonomy_mode` | `0`–`3`. [Who picks the next step](/concepts/executing-a-request/autonomy-modes) | Always. Defaults to `0` |
| `prompt_id` | The [prompt pack](/concepts/authoring-a-product/prompts) for LLM stages | Every active route |
| `tool_manifest` + `tool_manifest_version` | The pinned manifest of [capabilities](/concepts/authoring-a-product/capability) | Mode 1 and any mode 2/3 route with tools |
| `workflow_id` | The fixed stage list | Mode 2 and mode 3 |
| `max_loop_steps` | `CALL`/`DONE` budget | Mode 1 (defaults to `8` at Runtime when unset) |
| `policy_profile` | Risk bar that Layer ② confirmation reads | Always |
| `model_profile` | Model tier. FK to `dataplane.model_profiles` | Always |
| `activation_target` | Where Runtime runs, e.g. `http://agent-runtime-shared:3008/v1/runs` | Always in practice — Front Door dials it |
| `agent_client_id` | Workload identity pinned on the run | Optional |
| `required_claims` | Entitlement filter. Defaults to `[]` | Optional |
| `channels` | Channel filter. Defaults to `["web"]` | Optional |
| `chat_visible` | Whether the route appears in the chat eligible set | Defaults to `true` |
| `description` | Display text for the Control Plane | Optional |

**There is no `manifest_id` column.** The manifest pointer is the pair `tool_manifest` + `tool_manifest_version`.

Two companion tables are keyed by the same `(route_id, route_version)` and foreign-keyed back to the route: `dataplane.retrieval` (see [retrieval](/concepts/authoring-a-product/retrieval) and [corpus](/concepts/authoring-a-product/corpus)) and `dataplane.memory_profiles` (see [memory](/concepts/authoring-a-product/memory)).

### Fields the catalogue stores but nothing reads

Do not plan behaviour on these.

| Field | Reality |
| --- | --- |
| `keywords` | Stored on the row. **Layer ② does not score it.** The classifier indexes labelled seed utterances, not this column |
| `output_schema_id` | A pointer only. Runtime never loads it. Structured output comes from the capability `output_schema` — see [schema](/concepts/authoring-a-product/schema) |
| `eval_suite_id` | Catalogue metadata |
| `fallback` | Stored. No decide or Runtime path reads it |
| `model_profile` | Enforced as a foreign key and passed on the start contract, but **Runtime ignores it**. The model is global — see [LLM](/concepts/authoring-a-product/llm) |

## What each autonomy mode requires

`CataloguePinLint` enforces these at publish time, so a bad combination fails before a caller can hit it.

| Mode | Must have | Must not have |
| --- | --- | --- |
| `0` Single inference | `prompt_id` | `tool_manifest`, `workflow_id`, `retrieval.mode=tool` |
| `1` Autonomous | `prompt_id`, `tool_manifest` | `workflow_id` |
| `2` Deterministic | `prompt_id`, `workflow_id` | — |
| `3` Guided | `prompt_id`, `workflow_id`, `tool_manifest` | — |

Every active route needs a `prompt_id`, in every mode. There is no domain-HTTP-only product.

## Versions, `status`, and the pin

A `route_id` can have any number of versions. **Exactly one may be `active`** — a partial unique index enforces it, and a check constraint ties the two fields together: `active = true` if and only if `status = 'active'`.

| Status | Meaning |
| --- | --- |
| `draft` | Work in progress. Not hydratable |
| `published` | An immutable released cut. Not necessarily the live one |
| `active` | The version new requests classify against. One per `route_id` |
| `retired` | Taken out of service |

Only `active` rows participate in routing — decide and the eligible list both read `activeRoutes()`.

**Pinning** is what stops a mid-flight catalogue change from rewriting a running request. Once decide returns a `route_id` and `route_version`, Front Door fetches that exact row, writes a freeze, and starts Runtime with both. Runtime refuses to start without the version, copies the pair onto a durable run pin, and hydrates against that snapshot. Publishing a new active version afterwards does not affect a run already in flight.

## Authoring a route

**There is no write API.** The Data Plane exposes reads plus decide; the only `POST` is `/v1/intent/decide`. Routes are authored as SQL under `agent-fabric-scripts/stack/route/<route_id>/` and loaded by the seed script.

| Endpoint | Returns |
| --- | --- |
| `GET /v1/catalog/routes` | Active routes. `?include=all` for every version |
| `GET /v1/catalog/routes/{routeId}` | One route. `?route_version=` for an exact pin, omit for the active row |
| `GET /v1/catalog/routes/{routeId}/versions` | Every version of one route |
| `GET /v1/intent/eligible?channel=` | Chat-eligible active routes |

The response nests the resolved `manifest`, `retrieval`, and `memory_profile` alongside the route fields, so one GET is enough to see the whole product. The [Control Plane](http://localhost:3006) browses the same endpoints.

## How decide picks a route

`POST /v1/intent/decide` is Data Plane only, and only the `afd` workload may call it. It prunes the eligible set first, then walks three layers.

| Layer | Id | What it does |
| --- | --- | --- |
| ① Rules | `rules` | A named `route_id` (jobs, or a chat chip) or a slash command from `dataplane.intent_rules`. First match wins, and a named `route_id` **never** falls through |
| ② Classifier | `retrieve` | In-process nearest-neighbour over labelled utterances, on a 50 ms budget. Over budget means abstain, and ③ is skipped |
| ③ LLM fallback | `llm` | **Off by default.** The layer is a stub that returns nothing |

Eligible pruning differs by ingress: jobs and a named `route_id` see every active entitled route including hidden ones, while chat sees only `chat_visible` routes matching the channel and the caller's claims.

| Outcome | Meaning | Starts a run |
| --- | --- | --- |
| `route` | Binds `route_id`, `route_version`, `intent_label`, `confidence` | Yes |
| `clarify` | Returns a prompt and candidates | No |
| `abstain` | Nothing matched, or the classifier ran out of budget | No |

Only `route` pins. See [request lifecycle](/concepts/executing-a-request/request-lifecycle) for what happens after.

## Seed examples

Every stack seed uses `route_version = '2026.08.1'` with `active = true`.

| `route_id` | Mode | What it attaches |
| --- | --- | --- |
| `overdraft_fee_qa` | `0` | Prompt pack, plus `deterministic_prefetch` over `fee-schedule` and `product-disclosure` |
| `ticket_draft_reply` | `0` | Prompt pack. `chat_visible=false` — it is a child of `ticket_triage` |
| `fee_explain` | `1` | Manifest, `max_loop_steps=6` |
| `billing_assistant` | `1` | Manifest with `account_fee_lookup` and `lookup_order_by_order_id` |
| `duplicate_charge_review` | `2` | Manifest plus workflow |
| `kyc_onboarding` | `2` | Manifest plus a workflow with branch and `human_gate`. `chat_visible=false` |
| `ticket_triage` | `3` | Manifest plus a workflow with a `kind=agent` child into `ticket_draft_reply` |

Layer ① command seeds exist too: `/shopassist` binds `shopassist_case`, `/overdraft` binds `overdraft_fee_qa`.

The full matrix is [catalogue routes](/catalogue/routes); what actually executes is [coverage status](/catalogue/coverage-status).
