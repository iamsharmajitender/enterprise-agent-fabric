---
title: Identities
sidebar_label: Identities
description: "Three principals on every run: the user who asked, the agent acting as software, and the Runtime box. They never share a bearer."
---

# Identities

Every run has **three principals**. They answer different questions, hold different credentials, and must not collapse into one token.

The story: [how it hangs together](/how-it-hangs-together#what-it-governs). The authorization that hangs off the first two principals: [claims and scopes](/concepts/executing-a-request/claims-and-scopes).

| Principal | Answers | Used to call | In this stack |
| --- | --- | --- | --- |
| **User** | Who is asking? | Front Door only | Executed as channel claims |
| **Agent** | Which software is acting? | Shared Tools / domain APIs | Named on the route. Token mint is not built yet |
| **Runtime** | Which box is running the loop? | Catalogue and fabric internals | Executed as a workload identity |

The box is isolated by `activation_target`. The robot is named by `agent_client_id`. A new product is a new route and a new robot, not a new Runtime.

<div className="gain-diagram-wrap">

![The user entitles a route. The route pins the agent. Runtime hydrates the pin. Three principals, three bearers.](/diagrams/identity-and-trust.svg)

</div>

---

## User

The person or system at the channel. Front Door authenticates them. Data Plane entitles them. They never become the tool-call bearer.

Locally the channel presents a stub user and an entitlement set. Missing or invalid identity is a refusal: do not decide, do not start Runtime.

Jobs can carry a stored approval instead of live claims. Same principal, different envelope.

Production target: a real identity-provider user token. Same job — prove who is asking — still not the robot, still not the box.

---

## Agent

The software product acting on the user’s behalf. Named on the route. Frozen onto the run pin. Distinct from the user and from whichever Runtime box happens to execute.

After freeze, Runtime is supposed to ask the identity provider for a token **for that client**, downscoped to this route’s pinned tool actions. That bearer is what Shared Tools would see. The pin stores a pointer, never the raw token.

Mint order: **pin first, then agent token.** A later catalogue cut does not widen an in-flight bearer. Two routes that share a Runtime box still have two robots.

This stack stores the robot name on the pin and does not mint. Detail: [claims and scopes](/concepts/executing-a-request/claims-and-scopes#2-agent-scopes).

---

## Runtime

Every Runtime **box** has a workload identity so it can call fabric internals. That identity is per box, not per route. Many agents can share one Runtime. They do not share one agent bearer.

What the box may do:

| Call | Allowed |
| --- | --- |
| Catalogue GET at the **pinned** version | Yes |
| Registry GET of published manifests and capabilities | Yes |
| Classify a new request | No. Only Front Door may decide |
| Call a domain API as this bearer | No. Not a downstream principal |

Front Door starts Runtime as itself. Runtime then hydrates as the Runtime workload. A channel user token on either internal API is a refusal.

Production target: pod identity to Data Plane, Registry, identity provider (to mint the **agent** token), model router, and audit. Inward only.

The local header contract: [stub auth](/reference/stub-auth).

---

## Worked example

Jane asks about a double charge. Decide binds `duplicate_charge_review`. Three identities on that run:

| Principal | On this run |
| --- | --- |
| User | Jane, entitled for a support case |
| Agent | `agent-duplicate-charge-review` |
| Runtime | the custom box, hydrating the pinned catalogue |

Jane’s claim gets her **onto** the route. The robot would be minted with the four tool actions on that manifest. The box’s workload identity is what lets hydrate read the pinned row. None of those three is interchangeable.

---

## What runs today

| Step | Local |
| --- | --- |
| Channel user as stub claims | Yes |
| Entitle against the route | Yes |
| Freeze the robot name on the pin | Yes |
| Mint an agent token | No. Identity provider is a later cut |
| Runtime calls internals as a workload | Yes |
| Distinct workload certificate per box | No. Shared stub; only the header value differs |
| Agent or Runtime bearer on domain mocks | No. Tool calls send no authorization |

---

## Anti-patterns

- One agent token at Runtime boot with every route’s scopes.
- A new Runtime box per route only to get a different **agent** identity.
- Deriving the robot name from the route id instead of pinning an explicit pointer.
- The user bearer as the tool-call caller.
- The Runtime workload bearer as authorization to domain APIs.
- Treating “this process is Runtime” as permission to decide, or as the robot.
- Skipping the agent check because Front Door already entitled the user.

The box runs the loop. The robot acts. The user asked. Keep the three bearers apart.
