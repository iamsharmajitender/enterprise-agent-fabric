# Docs

Documentation for this repository. Behaviour is what Agent Runtime executes after pin and hydrate. Catalogue rows can name more than Runtime does; those gaps are labelled on the [status](02-understand/status.md) page.

## Shelves

| Shelf | What it holds |
| --- | --- |
| [01-start](01-start/README.md) | Run the local fabric |
| [02-understand](02-understand/overview.md) | How this binary works |
| [03-catalogue](03-catalogue/) | Catalogue routes and use cases (generated from the seed) |
| [04-architecture](04-architecture/) | Box packs (AFD, ADP, ACR, AR) plus [narrative/](04-architecture/narrative/) |
| [05-reference](05-reference/) | Frozen JSON contracts |

## Stays where it is

These directories are not shelves. They do not move.

| Path | Role |
| --- | --- |
| [run/](run/) | Operator scratchpad: Compose, start/stop/seed scripts, dummy jobs, tool-mock, runbooks |
| [tasks/](tasks/) | Engineering plans and todos |
| [intent/](intent/) | v1 lock: what to build. Not how a box works today |

## Reader paths

| You want | Start here |
| --- | --- |
| New you | [01-start](01-start/README.md), then [overview](02-understand/overview.md) |
| What can it do | [03-catalogue](03-catalogue/) |
| How a box works | [04-architecture](04-architecture/), then [02-understand](02-understand/overview.md) |
| Enhance later | [tasks/](tasks/), especially [dataflow-plan.md](tasks/dataflow-plan.md) |

## How this binary works

- [Overview](02-understand/overview.md) — five processes, pin then hydrate then linear LangGraph, jobs vs chat
- [Capabilities](02-understand/capabilities.md) — two kinds (`domain`, `agent`); do not add kinds for retrieve, prompts, or MCP
- [Patterns](02-understand/patterns.md) — Pattern 0–3 seed; workflow is a stage list; the graph is linear
- [Data](02-understand/data.md) — `goal` vs `notes`; HTTP is `dict(goal)` only; slots do not exist
- [Prompts](02-understand/prompts.md) — `prompt_packs` and `llm_role`
- [Retrieve](02-understand/retrieve.md) — named retrieve HTTP vs catalogue prefetch (no-op)
- [Memory](02-understand/memory.md) — `memory_profiles` policy vs what Runtime writes
- [Status](02-understand/status.md) — catalogue vs this Runtime
