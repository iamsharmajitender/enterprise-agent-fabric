---
title: Working on the docs
sidebar_label: Working on the docs
description: "How this documentation site is laid out, and how to regenerate it."
---

# Working on the docs

This page is for people editing the site, not for learning the platform. Start at the [home page](/) instead.

## Sections

| Section | For |
| --- | --- |
| [Guides](/running-locally) | Start the stack, send a request, author an agent |
| [Concepts](/concepts/glossary) | Vocabulary you attach to a route, and what happens when a request runs |
| [Architecture](/architecture/) | Why the fabric exists, who owns what, internals, one page per box |
| [Autonomy](/autonomy/) | Who picks the next step (modes 0–3) |
| [Use cases](/use-cases/) | Caller and process shapes |
| [Reference](/reference/) | Frozen fixtures and stub auth |

Engineering material that is **not** published with this site:

| Path | Role |
| --- | --- |
| [`tasks/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/tasks/) | Engineering plans |
| [`intent/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/intent/enterprise-agent-fabric-v1.md) | The v1 lock |
| [`diagram-sources/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-docs/diagram-sources/) | Diagram generators |
| [`agent-fabric-scripts/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-scripts/) | Compose and seed scripts |
| [`agent-fabric-mocks/`](https://github.com/iamsharmajitender/enterprise-agent-fabric/blob/main/agent-fabric-mocks/tools/) | Domain HTTP doubles |

## Run the site

```bash
cd agent-fabric-docs
npm install
npm start          # dev server with hot reload
npm run build      # production build; fails on broken links
npm run diagrams   # regenerate static/diagrams from diagram-sources/
```

Order in the sidebar comes from the numbered folders under `docs/` and the `_category_.json` beside them.
