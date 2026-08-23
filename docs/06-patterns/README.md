# Patterns

This shelf is the **intended pattern set**: what a route is allowed to be. It is not a dump of what Agent Runtime hydrates today. Gaps live on [status](../02-understand/status.md). Seed examples live in [03-catalogue](../03-catalogue/). How this binary hydrates: [02-understand/patterns](../02-understand/patterns.md).

There are **four** autonomy patterns. That integer is `autonomy_mode`. It answers **who picks the next step**. Retrieval, memory, tools, and ingress do not mint a fifth mode.

| File | Mode | Who picks the next step |
| --- | --- | --- |
| [single-inference](single-inference.md) | `0` | Nobody. One LLM call. No tools. |
| [autonomous](autonomous.md) | `1` | The LLM (`CALL` / `DONE`). Manifest required. |
| [deterministic](deterministic.md) | `2` | The workflow designer. Workflow required. |
| [guided](guided.md) | `3` | Designer for stages; LLM inside a stage allowlist. |

Every route still calls the LLM at least once. There is no domain-HTTP-only product. Each pattern page has **How it is hooked together** (route pins → hydrate → graph → attachments) and **How the LLM is called** (system/user, when `complete` runs).

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

Treat memory as **omit vs session** in this shelf. Do not explode `conversation` × `working` × `loop` × `long_term` into sixteen products.

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
