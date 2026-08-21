# Enterprise Agent Fabric — solution architecture packs

Four solution-architecture documents, one per Fabric box. Each pack is the **solution architecture** (artifacts 9–12) plus **detailed solution design** (artifacts 13–17) from [case-studies.md](../../case-studies.md). Packs 1–2 (brief, options) and 5–7 (security, operate, evolve) stay on the product pages until those are written.

**Source of truth for behaviour:** [docs/enterprise-agent-fabric](../enterprise-agent-fabric/). These packs restate that design so a CTO can scan a box in two minutes, and an engineer can implement it.

**Status:** Draft, aligned to the pin-split proposal (AFD pins and starts; Agent Plane classifies; AR runs). Playbooks that still put the pin on ACP are behind this paper.

## Documents

| Pack | Box | Job in one line |
| --- | --- | --- |
| [Agent Front Door](./agent-front-door.md) | Chat AFD + API AFD | Only way in. Entitle, freeze, start. Two fleets, one contract. |
| [Agent Plane](./agent-plane.md) | ACP + Agent Data Plane | Catalogue and classify. Does not pin or start AR. |
| [Agent Runtime](./agent-runtime.md) | AR + Shared calls | Does the work. Run pin, loop, Patterns 0–3. |
| [Agent Capability Registry](./agent-capability-registry.md) | Registry (with Agent Plane) | Publishers append `id@version`. AR hydrates at pin. |

Read order matches a request: **AFD → Plane → Runtime → Registry**.

## What each pack contains

Modified from case-studies §B–C. Security, SLO maths, and runbooks are **not** duplicated here; failure design is, because it is load-bearing for this fabric.

| # | Section in each pack | Case-study artifact |
| --- | --- | --- |
| — | Boundaries and non-goals | Added: this architecture is defined as much by what the box must not do |
| 9 | Solution on a page | Problem → requirements → architecture → tech choices → outcomes + one diagram |
| 10 | Context | Users, channels, this box, siblings, providers |
| 11 | Container / component | One level deeper than context |
| 12 | Deployment | AZs, networking, trust boundaries, scale, failover, ingress/egress |
| 13 | API design | Paths, bodies, auth, idempotency, errors, rate limits |
| 14 | Data architecture | Records, keys, TTL, indexes, consistency |
| 15 | Event / messaging | Topics, partition key, consumers, retries, DLQ, delivery |
| 16 | Sequences | Happy path, failure, duplicate / idempotent (minimum) |
| 17 | Failure and resilience | Component, network, dependency, duplicates, poison, shed, DR |

Diagrams are G.A.I.N editorial HTML/SVG in [`diagrams/`](./diagrams/) (not Mermaid). HTML is the source; SVG is inlined in the packs.

## Locked fabric rules these packs do not reopen

1. **Four jobs.** AFD entitles, pins, starts. Data Plane classifies and serves the catalogue. ACP is control + decision audit. AR runs and requests the agent token.
2. **Two AFD fleets, one contract.** Separate process (FR-9). `{runs_topic}` is AR return. Kafka job start is the API AFD.
3. **Jobs name `route_id`.** Skip classifier and clarify. Do not skip entitle + record.
4. **Generic chat still classifies.** Hints are eligible + chat-visible. A tap is Layer ①.
5. **Only `route` starts AR.** Clarify / abstain never pin. Default start is async `202`.
6. **One Agent Plane per trust domain.** Not one mega-agent.
7. **Three principals.** User ≠ agent ≠ AR workload. Dual check in Shared Tools / PEP.
8. **Capabilities are references.** AR hydrates the whole pinned manifest before the LLM. `kind=agent_start` invoke is API AFD, not the callee AR.

## Naming

Product pages mix NAFD/NACP with AFD/ACP. Product pages mix NAFD/NACP with AFD/ACP. These packs use the child-page names: **AFD**, **ACP**, **Agent Data Plane**, **AR** (Agent Runtime), **Registry**. Editorial HTML/SVG under `diagrams/` and `docs/enterprise-agent-fabric/` may still say NAR until those figures are redrawn.
