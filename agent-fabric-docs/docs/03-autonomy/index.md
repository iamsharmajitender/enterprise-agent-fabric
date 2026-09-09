---
title: Autonomy
sidebar_label: Overview
description: "The four autonomy modes and the orthogonal attachments (retrieval, memory, tools, workflow) that compose around them."
---

# Autonomy

This section is the **intended mode set**: what a route is allowed to be. It is not a dump of what Agent Runtime hydrates today. Gaps live on [status](/catalogue/coverage-status). Seed examples live in [catalogue](/catalogue/). How this binary hydrates: [autonomy modes](/concepts/executing-a-request/autonomy-modes).

There are **four** autonomy patterns. That integer is `autonomy_mode`. It answers **who picks the next step**. Retrieval, memory, tools, and ingress do not mint a fifth mode.

| Mode | Page | Who picks the next step |
| --- | --- | --- |
| `0` | [Single inference](/autonomy/mode-0-single-inference) | Nobody. One LLM call. No tools. |
| `1` | [Autonomous](/autonomy/mode-1-autonomous) | The LLM (`CALL` / `DONE`). Manifest required. |
| `2` | [Deterministic](/autonomy/mode-2-deterministic) | The workflow designer. Workflow required. |
| `3` | [Guided](/autonomy/mode-3-guided) | Designer for stages; LLM inside a stage allowlist. |

Every route still calls the LLM at least once. There is no domain-HTTP-only product. Each mode page has **How it is hooked together** (route pins → hydrate → graph → attachments) and **How the LLM is called** (system/user, when `complete` runs).

## Orthogonal attachments

These sit on the route beside `autonomy_mode`. Combining them is a **composition**, not a new pattern.

| Attachment | Omit | On |
| --- | --- | --- |
| Retrieval | no index | `deterministic_prefetch` (app packs `scope` before generate) or `tool` (named retrieve capability on the manifest) |
| Memory | one-shot | session policy: `conversation` + `working`; Pattern 1/2/3 may also author `loop=checkpoint`; `long_term=retrieve_only` only when retrieve exists |
| Tools | Pattern 0, or Pattern 2 LLM-only | ACR manifest (`domain` HTTP and/or `kind=agent` child start) |
| Workflow | Pattern 0 and 1 | Required on Pattern 2 and 3 |
| Ingress | — | jobs or chat. Not a pattern. |

`retrieval.mode=tool` is a domain capability. It is not a “no tools” variant. Pattern 0 cannot take it.

Treat memory as **omit vs session** here. Do not explode `conversation` × `working` × `loop` × `long_term` into sixteen products.

## Illegal combinations

| Combination | Why |
| --- | --- |
| Pattern 0 + manifest | Single inference never calls a domain API |
| Pattern 0 + workflow | One call has no stage list |
| Pattern 0 + `retrieval.mode=tool` | That is a tool |
| Pattern 1 + no manifest | The loop has nothing to `CALL` |
| Pattern 1 + workflow | The LLM picks the path; a stage list would fight it |
| Pattern 2/3 without workflow | Designer cannot pick the next step |
| Pattern 3 with no tools | An allowlist over an empty set |
| `long_term` without retrieve | Facts must be recalled, not stuffed into every prompt |
