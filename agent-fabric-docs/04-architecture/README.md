# Enterprise Agent Fabric — solution architecture

Box design docs for the Fabric. Each file is MDX with frontmatter, `gain-diagram-wrap` figures, and the full solution pack (deployment, APIs, data, sequences, failure).

These packs may be ahead of code. Behaviour of the running binary is [02-understand/status.md](../02-understand/status.md).

Playbook and Docusaurus slugs (`/intent/...`, `/playbooks/...`) inside MDX frontmatter are leftovers from the original site export. In this repo, use relative links between files in this folder.

**Status:** Draft, aligned to the pin-split proposal (AFD pins and starts; Agent Plane classifies; AR runs).

## Documents

| Pack | Box | Job in one line |
| --- | --- | --- |
| [Enterprise Agent Fabric](./enterprise-agent-fabric-architecture.mdx) | Whole fabric | One decide contract, two AFD fleets, three principals |
| [Enterprise Agent Fabric V1](./enterprise-agent-fabric-pitch.mdx) | Executive brief | One front door, many governed capabilities |
| [Agent Front Door](./agent-front-door.mdxx) | Chat AFD + API AFD | Only way in. Entitle, freeze, start. Two fleets, one contract. |
| [Agent Plane](./agent-plane.mdxx) | ACP + Agent Data Plane | Catalogue and classify. Does not pin or start AR. |
| [Agent Runtime](./agent-runtime.mdxx) | AR + Shared calls | Pin, hydrate, LangGraph loop, Patterns 0–3. |
| [Agent Capability Registry](./agent-capability-registry.mdxx) | Registry (with Agent Plane) | Publishers append `id@version`. AR hydrates at pin. |

Read order matches a request: **Fabric → AFD → Plane → Runtime → Registry**.

## What each box pack contains

| Section | What it covers |
| --- | --- |
| Solution on a page | Problem → requirements → architecture diagram → tech choices → outcomes |
| Context / job | Users, channels, siblings, providers |
| Container / component | One level deeper than context |
| APIs | Paths, bodies, auth, idempotency, errors |
| Deployment | AZs, networking, trust boundaries, scale, failover |
| Data architecture | Records, keys, TTL, indexes, consistency |
| Event / messaging | Topics, partition key, consumers, retries |
| Sequence diagrams | Happy path, failure, idempotent (with `gain-diagram-wrap` SVGs) |
| Failure and resilience | Component, network, dependency, poison, shed, DR |
| Scaling | Fleet signals and anti-patterns |

Diagrams: G.A.I.N editorial HTML/SVG in [`diagrams/`](./diagrams/) and fabric-level SVGs in this folder (`agent-fabric-*.svg`). HTML is the editorial source; SVG is inlined in MDX via `gain-diagram-wrap`.

## Locked fabric rules these packs do not reopen

1. **Four jobs.** AFD entitles, pins, starts. Data Plane classifies and serves the catalogue. ACP is control + decision audit. AR runs and requests the agent token.
2. **Two AFD fleets, one contract.** Separate process (FR-9). `{runs_topic}` is AR return. Kafka job start is the API AFD.
3. **Jobs name `route_id`.** Skip classifier and clarify. Do not skip entitle + record.
4. **Generic chat still classifies.** Hints are eligible + chat-visible. A tap is Layer ①.
5. **Only `route` starts AR.** Clarify / abstain never pin. Default start is async `202`.
6. **One Agent Plane per trust domain.** Not one mega-agent.
7. **Three principals.** User ≠ agent ≠ AR workload. Dual check in Shared Tools / PEP.
8. **Capabilities are references.** AR hydrates the whole pinned manifest before the LLM. `kind=agent` invoke is API AFD, not the callee AR.

## Naming

Docs use **AFD**, **ACP**, **AR**. Editorial SVG under `diagrams/` may still say NAR until those figures are redrawn.
