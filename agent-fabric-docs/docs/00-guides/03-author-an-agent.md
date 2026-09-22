---
title: Author an agent
sidebar_label: Author an agent
slug: /guides/author-an-agent
description: "What you write to put an agent on the fabric: a route, the rows it points at, and an autonomy mode."
---

# Author an agent

An agent on this platform is a **route** plus the rows that hang off it. You do not stand up a new chatbot, a new identity stack, or a new audit trail. You publish a capability, pin it on a route, and choose how much latitude the model gets.

## The rows you write

| You author | What it is | Page |
| --- | --- | --- |
| [Route](/concepts/authoring-a-product/route) | The product. Versioned. Only one version is `active`. | Route |
| [Capability](/concepts/authoring-a-product/capability) | A tool or child agent, published as `id@version` | Capability |
| [Prompts](/concepts/authoring-a-product/prompts) | What the model is told, by `llm_role` | Prompts |
| [Schema](/concepts/authoring-a-product/schema) | JSON Schema that binds model output | Schema |
| [Autonomy mode](/concepts/executing-a-request/autonomy-modes) | Who picks the next step (0–3) | Autonomy modes |
| [Retrieval](/concepts/authoring-a-product/retrieval) and [corpus](/concepts/authoring-a-product/corpus) | Optional grounding | Retrieval |
| [Memory](/concepts/authoring-a-product/memory) | Optional session / checkpoint flags | Memory |

[Audit](/concepts/authoring-a-product/audit) and [observability](/concepts/authoring-a-product/observability) are not route fields. They fire for every run.

## The transfer that matters

1. A domain publishes a capability as `id@version`. Published versions are immutable.
2. A route pins that version. The route is itself versioned.
3. A run pins the route version. Catalogue edits do not disturb work in flight.
4. The pin becomes evidence. You can ask what was running last Tuesday.

Today, routes and corpora are seeded from SQL under `agent-fabric-scripts/stack/route/`. Capabilities and manifests have a write API.

## What you do not author

- A second front door
- A per-agent identity provider
- A per-agent audit store
- Entitlements stored on the route row — those come from ingress claims

The platform owns the path. You own whether the agent is good. That split is the [operating model](/architecture/operating-model).

## Try it

Start from a seeded route such as `fee_explain` ([catalogue](/catalogue/routes)), send [a first request](/guides/first-request), then read the [route](/concepts/authoring-a-product/route) and [capability](/concepts/authoring-a-product/capability) pages for the fields you would change.
