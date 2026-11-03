---
title: Claims and scopes
sidebar_label: Claims and scopes
description: "User claims entitle a route. Agent scopes permit a tool. They are different principals, different moments, and they do not share a string."
---

# Claims and scopes

Two authorization layers sit on a request. **User claims** decide whether a [route](/concepts/authoring-a-product/route) is even eligible. **Agent scopes** decide which tools that route’s robot may invoke. They are not the same string, they are not checked at the same time, and holding one does not grant the other.

The three principals are [identities](/concepts/executing-a-request/identities). This page is the authorization contract that hangs off the first two. The story: [how it hangs together](/how-it-hangs-together#what-it-governs).

| Layer | Principal | When | In this stack |
| --- | --- | --- | --- |
| Route entitlement | **User** | Decide, before a pin | Executed |
| Tool permit | **Agent** | Before each invoke | Catalogue-only. No token mint, no enforcement point yet |

## User claims {#1-user-claims}

`required_claims` is the entitlement filter on the route. Decide prunes the eligible set **before** rules or a classifier run. A named `route_id` still has to survive that prune — jobs skip classify, they do **not** skip entitle.

The check is **all-of**: the caller’s claim set must contain every entry on the row. Fail closed. Missing the required claim drops the route from eligible. Decide returns `abstain`. Front Door does not pin. Runtime does not start. Chat UI never sees the route id.

`required_claims` is **not** a tool permission. Passing it means “this person may start this product.” It does not mint an agent token and it does not permit a refund post.

| Ingress | Eligible set |
| --- | --- |
| Jobs, or chat with a named route | Every **active** row the caller is entitled to |
| Chat classify | Chat-visible ∩ channel ∩ claims |

Local stub shape: [stub auth](/reference/stub-auth).

## Agent scopes {#2-agent-scopes}

A published [capability](/concepts/authoring-a-product/capability) is not permission. The tool permit sits on the **manifest reference** — agent policy, not the capability row.

On a duplicate-charge review the user claim is `support:case`. The action on the respond tool is `duplicate_charge_respond`. Those strings are not a join.

**Production target.** After Front Door freezes the route and the robot name, Runtime copies the pin, **then** asks the identity provider for a token for that client, **downscoped to this route**. “This route” means the frozen manifest’s action list — not every action the client might be registered for, and not every other route that happens to share compute.

Mint order: **pin first, then agent token.** A later catalogue cut does not widen an in-flight bearer.

Shared Tools then dual-checks **every** invoke:

| Check | Question |
| --- | --- |
| User | May this person (or this stored approval) perform the action? |
| Agent | May this robot perform the action? |

Runtime proposes. Shared enforces. The Runtime workload identity is not the tool-call bearer.

## Worked example

Jane is entitled `support:case`. Decide may bind `duplicate_charge_review`. After freeze, the intended agent token would carry **only** the four tool actions on that manifest — intake, lookup, investigate, respond.

Jane’s `support:case` is not on that list. `duplicate_charge_respond` is not on Jane’s entitlements. Both must pass in production. Locally only the first check runs; the tools then invoke with no bearer.

A billing assistant is the contrast: its user entitlement is a different all-of set, and its tool actions are a different list.

## What is not a scope

| Field | What it actually does |
| --- | --- |
| `required_claims` | User entitlement at decide |
| `channels` | Ingress filter. Orthogonal to claims |
| `chat_visible` | Whether chat classify may see the row. Jobs still can |
| `policy_profile` | Classifier confidence bar. Not a token scope |
| `risk_tier` | Agent-policy metadata next to the tool action. Unused locally |
| `activation_target` | Which Runtime box runs. Not identity |
| `agent_client_id` | Which robot to mint **for**. Not the scope list itself |

Do not derive the robot name from the route id. The catalogue pins an explicit pointer so two products can share a box without sharing a bearer.

## Anti-patterns

- One agent token at Runtime boot with every route’s scopes.
- A new Runtime box per route only to get a different identity.
- The user bearer as the tool-call caller, or skipping the agent check because Front Door already entitled the user.
- Runtime workload identity as authorization to downstream APIs.
- Treating a tool action as a synonym for a user claim.
- Widening a minted token when the catalogue publishes a new manifest version.

## What runs today

| Step | Local |
| --- | --- |
| Entitle on decide | Yes |
| Freeze the robot name on the pin | Yes. Stored for audit |
| Mint a downscoped token | No |
| Dual-check before invoke | No. Domain mocks see no bearer |

Until the enforcement point exists, a caller who can start a route can run every tool on that pin. That is a known gap, not a hidden one.
