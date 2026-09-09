---
title: Documentation map
sidebar_label: Documentation map
sidebar_position: 0
slug: /
description: "Where everything lives: concepts you author against, the architecture of the boxes, the four autonomy modes, and the reference material behind them."
---

# Documentation map

Documentation for the Enterprise Agent Fabric. **Behaviour is what Agent Runtime executes after pin and hydrate.** The catalogue can name more than Runtime does; every gap is labelled on [coverage status](/catalogue/coverage-status).

## Start here

| You want | Go to |
| --- | --- |
| Run the fabric on this machine | [Running locally](/running-locally/) |
| The words this project uses | [Glossary](/concepts/glossary) |
| What a request actually does | [Request lifecycle](/concepts/executing-a-request/request-lifecycle) |
| What I can build | [Generic shapes](/use-cases/generic-shapes), then [Autonomy](/autonomy/) |
| How a box works | [Service packs](/architecture/service-packs/agent-front-door) |
| Why this exists at all | [The idea](/architecture/the-idea) |

## Sections

### [Concepts](/concepts/glossary)

The vocabulary, split by when you need it. **[Authoring a product](/concepts/authoring-a-product/route)** is everything you attach to a route: [route](/concepts/authoring-a-product/route), [capability](/concepts/authoring-a-product/capability), [prompts](/concepts/authoring-a-product/prompts), [schema](/concepts/authoring-a-product/schema), [retrieval](/concepts/authoring-a-product/retrieval), [memory](/concepts/authoring-a-product/memory), [LLM](/concepts/authoring-a-product/llm), [audit](/concepts/authoring-a-product/audit), [observability](/concepts/authoring-a-product/observability), and [corpus](/concepts/authoring-a-product/corpus). **[Executing a request](/concepts/executing-a-request/request-lifecycle)** is what the running fabric then does with it: the [lifecycle](/concepts/executing-a-request/request-lifecycle), the [autonomy mode](/concepts/executing-a-request/autonomy-modes) that picks the next step, the [run data](/concepts/executing-a-request/run-data) crossing stage boundaries, and the [identifiers](/concepts/executing-a-request/identifiers) you trace it by.

### [Architecture](/architecture/)

[The idea](/architecture/the-idea) is the pitch. [Operating model](/architecture/operating-model) is who owns what. [Technical design](/architecture/technical-design) is the whole-fabric design. [Service packs](/architecture/service-packs/agent-front-door) are one solution pack per deployable box. These packs may be ahead of code.

### [Autonomy](/autonomy/)

The four modes, and what each one costs you in control: [Mode 0 — Single inference](/autonomy/mode-0-single-inference), [Mode 1 — Autonomous](/autonomy/mode-1-autonomous), [Mode 2 — Deterministic](/autonomy/mode-2-deterministic), [Mode 3 — Guided](/autonomy/mode-3-guided). The integer is `autonomy_mode` on the route, and it answers exactly one question: **who picks the next step**.

### [Use cases](/use-cases/)

Intended caller and process shapes — documents via DMS versus byte upload, an LLM review signal versus a process gate versus an async handoff. Not a dump of seed routes.

### [Catalogue](/catalogue/)

The active seed as a matrix: [routes](/catalogue/routes), [seed use cases](/catalogue/seed-use-cases), and the honest [coverage status](/catalogue/coverage-status) of catalogue versus this Runtime.

### [Reference](/reference/)

Frozen request and response fixtures, plus the [stub auth](/reference/stub-auth) headers. Not a live OpenAPI spec.

### [Running locally](/running-locally/)

Start the Compose stack, seed the catalogue, and follow a request through Grafana.

## Not part of this site

These live in the repository beside the site and are engineering material, not published documentation.

| Path | Role |
| --- | --- |
| [`tasks/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/) | Engineering plans and todos |
| [`intent/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/intent/enterprise-agent-fabric-v1.md) | The v1 lock: what to build |
| [`diagram-sources/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/diagram-sources/) | Python generators for the diagrams in `static/diagrams/` |
| [`agent-fabric-scripts/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-scripts/) | Compose, start/stop/seed scripts, dummy requests |
| [`agent-fabric-mocks/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-mocks/tools/) | Domain HTTP doubles on `:3010` |

## Working on the docs

```bash
cd agent-fabric-docs
npm install
npm start          # dev server with hot reload
npm run build      # production build; fails on broken links
npm run diagrams   # regenerate static/diagrams from diagram-sources/
```

Order in the sidebar comes from the numbered folders under `docs/` and the `_category_.json` beside them. Add a page and it appears — there is no sidebar list to maintain by hand.
