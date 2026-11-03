---
title: Author an agent
sidebar_label: Author an agent
slug: /guides/author-an-agent
description: "What you write to put an agent on the fabric: a route, the rows it points at, and an autonomy mode."
---

# Author an agent

:::note Local runbook
This page is how you publish. The story is [how it hangs together](/how-it-hangs-together). Who owns the path versus the work: [operating model](/architecture/operating-model).
:::

An agent on this platform is a **route** plus the rows that hang off it. You do not stand up a new chatbot, a new identity stack, or a new audit trail. You publish a capability, pin it on a route, and choose how much latitude the model gets.

## The rows you write

| You author | What it is | Page |
| --- | --- | --- |
| [Route](/concepts/authoring-a-product/route) | The product. Versioned. Only one version is `active`. | Route |
| [Capability](/concepts/authoring-a-product/capability) | A tool or child agent, published as `id@version` | Capability |
| [Prompts](/concepts/authoring-a-product/prompts) | What the model is told, by `llm_role` | Prompts |
| [Schema](/concepts/authoring-a-product/schema) | JSON Schema that binds model output | Schema |
| [Autonomy mode](/concepts/executing-a-request/autonomy-modes) | Who picks the next step (0–3) | Autonomy modes |
| [Claims and scopes](/concepts/executing-a-request/claims-and-scopes) | `required_claims` on the route; `pdp_action` on each tool | Claims and scopes |
| [Identities](/concepts/executing-a-request/identities) | User, agent (`agent_client_id`), Runtime box. You pin the robot, not the box | Identities |
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
- The caller's entitlements — those arrive as ingress `emts`. You do author `required_claims` on the route; see [claims and scopes](/concepts/executing-a-request/claims-and-scopes)

The platform owns the path. You own whether the agent is good. That split is the [operating model](/architecture/operating-model).

## Try it

Start from a seeded route such as `fee_explain`, send [a first request](/guides/first-request), then read the [route](/concepts/authoring-a-product/route) and [capability](/concepts/authoring-a-product/capability) pages for the fields you would change.
