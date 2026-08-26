# Future enhancements

Deferred work that is **not** on the v1 list in [todo.md](./todo.md). Remaining handbook tasks (25–29) and the root README (24) stay there.

Docs map: [docs/README.md](../README.md).

**Active follow-on (separate task lists):** Agent evals (routing golden set, jobs entitle, pin lint) — [eval-plan.md](./eval-plan.md) and [eval-todo.md](./eval-todo.md). Layered intent router I1–I11 + packaging — [intent-plan.md](./intent-plan.md) and [intent-todo.md](./intent-todo.md) (Layer ③ **on** is deferred here as I12). Those lists do not replace v1 todos.

**Done (signed off):**
- Observability O1–O16 — [observability-plan.md](./observability-plan.md) / [observability-todo.md](./observability-todo.md)
- Route-contract stage data sharing D1–D13 — [dataflow-plan.md](./dataflow-plan.md) / [dataflow-todo.md](./dataflow-todo.md)

Also parked here: [versioned route table](#versioned-route-table), [Front Door review follow-ups](#front-door-review-follow-ups), [Shared Memory](#shared-memory-conversation-and-long_term) (**both** `conversation` and `long_term`), [I12 Layer ③ LLM fallback](#i12-layer-3-llm-fallback).

---

# I12: Layer ③ LLM fallback (on decide)

<a id="i12-layer-3-llm-fallback"></a>

**Status:** Future enhancement (deferred from [intent-todo.md](./intent-todo.md#task-i12-structured-json-fallback-when--is-maybe--high-risk))  
**Date:** 2026-08-26  
**See also:** [intent-plan.md](./intent-plan.md) present-vs-remaining ③ row; layered classifier playbook

Decide already has the **plumbing** for Layer ③ (I10 port, I11 bounded pool + 500 ms timeout). The **flag stays off** (`fabric.decide.llm.enabled=false`). I12 is the work to turn that path **on** for real classify traffic.

## What it will offer

When Layer ② retrieve is **not confident enough** (maybe-band score or high-risk top candidate), decide will call a model once and ask it to pick among **eligible `route_id`s only**:

| Offer | Detail |
| --- | --- |
| **Ambiguous utterance → better `route` or `clarify`** | Today ② maybe / high-risk often ends in `clarify` or `abstain`. With I12, a rare LLM call can choose a single eligible id (or return top-k for `clarify`) instead of giving up. |
| **Eligible-ids-only contract** | The model cannot invent a route. Prompt / response JSON is constrained to the same entitled set ①/② already see. Invalid id → `abstain`. |
| **Confident ② stays free** | Fee-style unique winners at risk bar still **never** call ③. Jobs and named `route_id` bind still **never** call ③. |
| **Fail-closed under load** | Existing I11 timeout / queue reject still shed to `abstain` with `router_layer=llm` — decide must not hang on a slow model. |
| **Trace** | Decide events keep `router_layer=llm` and `latency_ms`. Chat FR-5 still strips these from assistant JSON. |

It does **not** offer: free-form chat answers, tool calling, Layer ④ safety (injection/PII veto), or using ③ as the primary classifier.

## What v1 does instead

```text
eligible → ① rules → ② retrieve → abstain / clarify
                              ↑
                    ③ port exists, flag OFF — never invoked
```

- Confident `$42` → `fee_explain` via ② (`router_layer=retrieve`).
- Maybe / high-risk / OOD / over-budget → `clarify` or `abstain` **without** an LLM.
- Operators keep local Compose safe: default flag off, no model gateway required for demos.

## When to revive

Reopen I12 when:

- Seeded maybe-band or high-risk utterances need a second chance before `abstain`.
- Eval / ops show too many false `clarify`s that a constrained JSON pick would fix.
- A model gateway (or stub adapter) is available with a hard timeout budget.

## Sketch (not on by default)

1. Leave `fabric.decide.llm.enabled` **false** in Compose / local defaults.
2. When flag **true**: after ② maybe or high-risk top candidate only, submit to I11 pool with eligible id list in the prompt.
3. Parse structured JSON `{ "route_id": "…" }` or top-k candidates → `route` / `clarify` / `abstain`.
4. Keep fee confident path and jobs path unit-tested as “③ never called.”
5. Acceptance: [intent-todo I12](./intent-todo.md#task-i12-structured-json-fallback-when--is-maybe--high-risk) checkboxes.

## Out of scope for this proposal

- Layer ④ safety plane (separate plan).
- Showing `router_layer` on chat wire JSON (FR-5).
- Running ③ on the Layer ② CPU path / blocking the decide thread beyond I11 timeout.
- Training or fine-tuning; HTTP to a gateway with eligible ids is enough for the first cut.

---

# Versioned route table

**Status:** Proposal  
**Date:** 2026-08-21

v1 versions each route on its own (`route_id` + `route_version`) and marks one row `active` per route. Classify uses every currently active route. A session pin is `route_id` + `route_version`. There is no `route_tables` snapshot.

This document is the deferred design: freeze the **whole contest board** as one published cut.

## Why consider it later

A route is a complete workflow. Pinning Jane’s “yes” only needs that workflow’s row. Fee explain and payments should not share a release train just to change a prompt or a tool.

Classify is different. The first turn is a contest among eligible routes. Who wins “Why was I charged $42?” depends on **every** contestant’s keywords and claims, not only on `fee_explain`. Independently publishing payments can change the fee winner without the fee route changing.

A route table version is a named reprint of that contest:

| Field | Role |
|---|---|
| `product` | Which assistant / UX domain owns the board |
| `route_table_version` | One id for the whole set (e.g. `2026.08.1`) |
| `active` | Which reprint new chats classify against |

Promote = insert a new cut, flip `active`. Rollback = point `active` at the previous cut. Eval and replay use one number for “who sat the test that day.”

## What v1 does instead

- `dataplane.routes` is keyed by `(route_id, route_version)`.
- At most one `active` version per `route_id`.
- `GET /v1/catalog/routes` lists active rows only.
- `POST /v1/intent/decide` scores the active mix.
- Follow-up pin (when Front Door stores it): `route_id` + `route_version`.

Teams can publish a route without waiting on other routes. The live mix is whatever each route last activated.

## When to revive the table

Revisit if any of these become painful:

- A misroute cannot be replayed because the mix of independently published routes is unknown.
- Payments shipping poisons fee questions and there is no one-flip rollback of the contest.
- Golden-set eval needs a certified label set, not “latest of each.” Until a table exists, the eval fixtures record the labelled mix in the file header ([eval-plan.md](./eval-plan.md)).
- Adding or removing a route should be an atomic catalogue publish.

## Sketch (not in v1)

Keep per-route `route_version`. Add `route_tables` as a **pointer set**, not a copy of workflow internals:

```text
route_tables
  route_table_version  2026.09.1
  product              corporate-assistant
  active               true

route_table_members
  route_table_version  2026.09.1
  route_id             fee_explain
  route_version        2026.08.1
  route_id             agent-payments-v2
  route_version        2026.09.1   -- payments shipped alone; fee stayed
```

New chats classify against the active table’s members. Jane’s pin stays `fee_explain@2026.08.1`. Payments can still version independently; the table only records **which editions share the contest**.

Do not merge fee and payments into one workflow. The table is composition of independently versioned routes.

## Out of scope for this proposal

- Implementing `route_tables` or a publish/activate API.
- Changing capability, manifest, or prompt versioning.
- Session stickiness in Front Door (still a separate follow-up).

---

# Front Door review follow-ups

**Status:** Parked  
**Date:** 2026-08-21  
**Source:** jobs + chat review of `agent-front-door`

None of these block the local `fee_explain` demo (`POST /v1/jobs` then GET, or chat turn until the canned fee line). Handbook drift is Task 29, not this list.

## Suggestions

- **Bind freeze rows to `sub`.** `GET /v1/assistant/sessions/{id}/events` does not read claims. Stub bearer is caller-asserted (`X-Stub-Claims`), so any stub client who knows a `session_id` can poll. Before a real IdP: store `sub` on the freeze row; pass claims into `events` and reject a mismatch.
- **Treat only HTTP 202 as Runtime start success.** `HttpRuntimeClient.start` accepts any 2xx with `correlation_id`. The Front Door README says non-202 → 503. Tighten the client to 202 only.
- **Skip AR open-run on a newly minted `sess-*`.** `AssistantService.turn` calls `GET /v1/runs?session_id=` even when this request minted the id. Skip that lookup when the session was just created.
- **Stronger HTTP FR-5 tests.** Controller tests substring-match `"route_id"` and similar keys. Reuse the recursive key scanner from `AssistantServiceTest`. Add controller coverage for clarify and continuation.
- **Jobs idempotency unique index.** Pack wants a unique TTL index on jobs `idempotency_key`. Today uniqueness is `session_id` (jobs use `job:{key}`). Add a constrained index when freeze schema is next touched.

## Spec gaps (Important, not v1 demo blockers)

- **Jobs Layer ① ignores channel.** Jobs with an explicit `route_id` now entitle active catalogue ∩ claims (no `chat_visible`, no Layer ②). `claims_adjudicate` + `claims:read` routes. Remaining: Front Door still hardcodes `channel: "web"`; this path does not filter `channels`. Later: send channel `api` (or the caller’s channel) and entitle catalogue ∩ claims ∩ channel.
- **Chat can resume a jobs freeze.** Jobs store `job:{idempotency_key}` in the same freeze table chat uses as `session_id`. A chat caller can POST `session_id: "job:…"` and resume or poll without decide. Later: mint/accept only `sess-` on assistant routes; reject `job:` with 400; add a test that `/v1/assistant/turns` does not resume a jobs row.
- **JDBC freeze store has no tests.** Production is `JdbcFreezeStore` (TTL 45 min, upsert, opaque ids). Automated freeze tests use `InMemoryFreezeStore` only. Later: Flyway-backed tests for save → get, TTL miss, and `putOpaque` / `resolveOpaque`.

---

# Shared Memory (conversation and long_term)

**Status:** Future enhancement (both deferred)  
**Date:** 2026-08-22 (updated 2026-08-26)  
**See also:** root [README Memory](../../README.md#memory), [memory.md](../02-understand/memory.md)

Catalogue `memory_profile` has four fields. Runtime already persists **`working`** (`{ notes, slots }` on `ar.runtime.runs.working`) and **`loop`** (`ar.runtime.runs.checkpoint`, including crash resume) when the route asks for them.

**Both of these remain future enhancements — catalogue-only until a Shared Memory box exists:**

| Field | Intent | DB today | Future store |
| --- | --- | --- | --- |
| **`conversation=session`** | Prior user/assistant turns in the next LLM call | **None.** Policy flag only on `dataplane.memory_profiles` | Shared Memory session transcript |
| **`long_term=retrieve_only`** | Facts for a later journey (not every prompt) | **None.** Policy flag only | Shared Memory / RAG collection |

Do **not** store either on `adp`, `ar`, `afd`, or `acr`. Same-run stage JSON handoff (`goal` / `slots` / `notes`, prefetch pack) is **not** this box — that track is done: [dataflow-plan.md](./dataflow-plan.md).

## Why consider it later

Chat history and recallable facts outlive one `correlation_id`. Jane’s `sess-88` can span many runs. Architecture puts Memory / RAG in **Shared**, keyed by isolation (`tenant`, `user`, `session`), so:

- routing still works if Memory is down (degraded chat, no history)
- AR is not the system of record for PII transcripts
- Jane cannot read John’s memory

Stuffing transcripts into `ar.runtime.runs` would mix “this pipeline’s scratchpad” with “what Jane said yesterday” and die with the run pin.

## What v1 does instead

- `dataplane.memory_profiles` records intent (`conversation=session`, `long_term=retrieve_only`, TTL, isolation) — **policy only**.
- Front Door freeze (`afd.frontdoor.freeze` locally; Redis in prod) is route stickiness, not a transcript.
- Graph `notes` + `slots` for **this** run go to `working` when `working=session`. Loop cursor (+ `resume_index`) goes to `checkpoint` when `loop=checkpoint`. `/v1/runs/{id}/turns` reloads `working` (notes/slots), not utterances.
- `/turns` does **not** prepend prior user/assistant utterances. A second `chat_session` turn does not see turn 1.
- Prefetch is **not** `long_term` — packs land in `working.slots.prefetch` for the same run only.

## When to revive

Revisit when any of these become painful:

- Multi-turn `chat_session` / `policy_chat` cannot answer “what was my account id?” after turn 1. → **`conversation`**
- A later job or chat must recall a fact from an earlier journey without stuffing the whole transcript into the prompt. → **`long_term`**
- Compliance needs session transcripts outside the run pin, with tenant isolation and TTL. → **`conversation`** (and possibly audit exports)

## Sketch (not in v1)

A fifth store (not one of `afd` / `adp` / `ar` / `acr`):

| Collection | Profile | Key | Write | Read |
| --- | --- | --- | --- | --- |
| Session transcript | `conversation=session` | `tenant` / `user` / `session_id` | After each chat turn: `{role, text, ts}` | Next turn: prepend to the LLM user blob. Jobs: skip unless you add follow-ups. |
| Long-term facts | `long_term=retrieve_only` | Same isolation, separate collection | After the run: summaries / facts, not full notes | Only via a retrieve tool (or prefetch). Never auto-inject into every prompt. |
| (omit / `none`) | no row, or field `none` | — | Do not write | — |

Honor `ttl_hours` (seed: 24 typical, 8 for KYC/dispute) and `isolation`. Prove **`conversation`** on `chat_session` with a stable `session_id` before wiring **`long_term`**.

## Out of scope for this proposal

- Implementing Shared Memory or a RAG index.
- Moving `working` / `loop` off `ar.runtime.runs`.
- Treating freeze Redis as conversation memory.
- Putting transcripts in files or in-process maps.
- Confusing prefetch / working slots with `long_term` recall.
