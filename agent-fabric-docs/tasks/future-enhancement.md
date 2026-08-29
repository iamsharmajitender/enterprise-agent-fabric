# Future enhancements

Deferred work that is **not** on the v1 list in [todo.md](./todo.md). Remaining handbook tasks (25–29) and the root README (24) stay there.

Docs map: [README.md](../README.md).

**Active follow-on (separate task lists):** Agent evals (routing golden set, jobs entitle, pin lint) — [eval-plan.md](./eval-plan.md) and [eval-todo.md](./eval-todo.md). Layered intent router I1–I11 + packaging — [intent-plan.md](./intent-plan.md) and [intent-todo.md](./intent-todo.md) (Layer ③ **on** is deferred here as I12). Agent audit (evidence chain; AADP + AACP) — [audit-plan.md](./audit-plan.md) and [audit-todo.md](./audit-todo.md). Generic tool failures (business/technical envelope + runtime policy) — [tool-failure-plan.md](./tool-failure-plan.md) and [tool-failure-todo.md](./tool-failure-todo.md). Those lists do not replace v1 todos.

**Done (signed off):**
- Observability O1–O16 — [observability-plan.md](./observability-plan.md) / [observability-todo.md](./observability-todo.md)
- Route-contract stage data sharing D1–D13 — [dataflow-plan.md](./dataflow-plan.md) / [dataflow-todo.md](./dataflow-todo.md)
- Agent audit A1–A16 (Phase 0–4; Kafka A17–A18 still parked) — [audit-plan.md](./audit-plan.md) / [audit-todo.md](./audit-todo.md)

Also parked here: [versioned route table](#versioned-route-table), [Front Door review follow-ups](#front-door-review-follow-ups), [Shared Memory](#shared-memory-conversation-and-long_term) (**both** `conversation` and `long_term`), [I12 Layer ③ LLM fallback](#i12-layer-3-llm-fallback), [platform hardening (bank readiness)](#platform-hardening-bank-readiness).

IdP / PEP / policy dual-check, Shared Memory, and a model router are **out of this hardening list** (handled separately or already parked above). Chat discoverability (utterances / Layer ②) stays on the intent track.

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

---

# Platform hardening (bank readiness)

<a id="platform-hardening-bank-readiness"></a>

**Status:** Future enhancement (architecture is bank-shaped; binary is a local foundation)  
**Date:** 2026-08-26  
**See also:** [status.md](../02-understand/status.md), [agent-runtime.md](../04-architecture/agent-runtime.md), [dataflow-plan.md](./dataflow-plan.md), hydrate in `agent-runtime/app/agents/hydrate.py`

EAF’s locked fabric rules (AFD pin → ADP catalogue → ACR capabilities → AR execute) are a credible **target platform spine** for bank agentic work. The gaps below are what turn “compose demo + content plugs” into a platform a bank can **standardize on and harden**. They are **not** more Patterns; they are fidelity, evidence, publish, and production posture.

**Suggested order when revived:** (1) hydrate fidelity → (2) publish lint / dual-store resolve → (3) evidence chain — **active track:** [audit-plan.md](./audit-plan.md) / [audit-todo.md](./audit-todo.md) → (4) side-effect invoke policy → (5) asserting mocks (stage I/O evidence is audit Phase B) → (6) release train / activate split → (7) HA / fleets / egress / chaos.

**Explicitly not in this section:** IdP / PEP / policy, `conversation` / `long_term` ([Shared Memory](#shared-memory-conversation-and-long_term)), model router (add later as its own cut), Layer ③ ([I12](#i12-layer-3-llm-fallback)).

---

## 1. Hydrate fidelity — catalogue truth = runtime truth

### Why it is needed

Banks treat a seeded `human_gate` or prefetch stage as a **control**. If hydrate drops those stages unless a workflow happens to declare `branch` (or has no manifest), the catalogue lies: risk and audit believe a pause or pack exists, and the run never hits it. Silent skip is a control failure, not a cosmetic bug.

### What v1 does instead

- Manifest routes: full workflow order / `human_gate` / tool-less stages only when `_workflow_has_branch` is true; otherwise manifest order + `llm_role` stamps (`hydrate.py`).
- Prefetch packing requires stage id literally `"prefetch"` plus `retrieval.mode=deterministic_prefetch`.
- Unknown `llm_role` fails at graph build; dropped stages do not.

### When to revive

- Any route with gates or prefetch must be trusted in ops / risk review.
- Contract tests show hydrated node ids ≠ workflow stage ids.
- Seed comments still say “catalogue-only” for gates that `status.md` claims execute.

### Sketch

1. **Single hydrate path:** when `workflow_id` is set, always build nodes from **workflow stage order**; manifest only supplies capability pins.
2. Unsupported `type` / `llm_role` / prefetch without retrieval → **hydrate fail closed** (no 202).
3. Seed / CI contract: for every catalogue route, hydrated stage ids == workflow stage ids (presence + order).
4. Optional: persist hydrate snapshot hash on the run pin for replay.

### Out of scope here

- Changing Pattern semantics; only making stored workflow executable or rejected.

---

## 2. Dual content stores (ADP + ACR) — publish resolve

### Why it is needed

Split catalogue journey (ADP) from published capabilities (ACR) is the right design. Ops pain is **two authoring surfaces, one pin**. Drift → hydrate 422 in “prod,” or humans patch only one Flyway file. Banks need one **publish unit** and automated proof that pointers resolve.

### What v1 does instead

- Route rows in `adp` point at `tool_manifest` + versions; AR `get_manifest` / `get_capability` hit **ACR only**.
- Seeds duplicate manifest/capability content across `V1__dataplane.sql` and `V1__registry.sql` by hand.
- No CI “pin resolve” gate beyond runtime hydrate failure.

### When to revive

- More than one team publishes routes or capabilities.
- Dual SQL / dual PR drift becomes the default failure mode.
- Rollback / promote must be “one cut,” not tribal sync.

### Sketch

1. Keep two stores; add a **release artifact** (single source → both migrations, or publish API).
2. **`fabric publish lint`:** every route’s manifest and each tool pin resolves in ACR; fail on missing/yanked.
3. Route versions never mutate capability pins in place — new cut → new manifest version.
4. Control Plane “pin health”: route → manifest → caps, red if unresolved.

### Out of scope here

- Merging ADP and ACR into one database.
- [Versioned route table](#versioned-route-table) (contest-board snapshot is related but separate).

---

## 3. Audit / decision record — evidence chain

**Active track (do not implement from this sketch alone):** [audit-plan.md](./audit-plan.md) · [audit-todo.md](./audit-todo.md).

### Why it is needed

Banks ask for more than “the agent answered.” They need **why this route**, under what entitlement snapshot, **which frozen contract** ran, and **what each stage saw/wrote**. v1 intent deferred decision audit (`/v1/decisions`). Freeze + correlation help; they are not a full evidence chain. IdP elsewhere does not replace fabric evidence. OTel is ops, not an append-only exam trail.

### Confirmed shape (see plan)

- **agent-audit-data-plane** (:3012, Java, DB `audit`) — append-only ingest + query.
- **agent-audit-control-plane** (:3013, TypeScript, no DB) — ops UI; only calls AADP.
- Producers AFD / ADP / AR / ACR → AADP via **async non-blocking HTTP**; Kafka later (same envelope).
- **Phase A:** decide, freeze/pin, hydrate snapshot, run terminal. **Phase B:** stage digests + ACR publish events.

### What v1 does instead

- No `/v1/decisions`; no audit table on `adp` / `ar`.
- Freeze + OTel only; chat FR-5 stays slim.

### Out of scope here

- Full SIEM; Shared Memory transcripts; `router_layer` on chat wire; implementing from this summary instead of the audit todo.

---

## 4. Side-effect tools — invoke policy

> **Related active track:** classifying tool outcomes (business vs technical, retryable) and a domain-free AR policy table lives in [tool-failure-plan.md](./tool-failure-plan.md) / [tool-failure-todo.md](./tool-failure-todo.md). This section keeps **capability `side_effect` / timeout / retry fields** — the gate for *whether* a classified `transient` retry is allowed on mutators.

### Why it is needed

Refunds, freezes, limit changes are **once-only or carefully idempotent**. Blind HTTP retry double-posts money movers. Mocks that ignore bodies teach false confidence (`--all` green ≠ correct hop). Architecture packs already describe risk-tier retries; the binary and capability contract do not yet enforce them.

### What v1 does instead

- Capabilities carry `invoke` + schemas; limited or no first-class `side_effect` / retry / timeout policy on the pin.
- agent-fabric-mocks often return canned bodies and ignore request JSON (except prefetch collection).
- Dataflow D-track proved slots/schema merge; dummy completed is still not full domain proof.

### When to revive

- Any production mutating tool (POST refund, freeze, KYC start).
- Need to fail closed on uncertain timeout for `once` operations.
- Contract tests must assert tool input and echo ids for stage N+1.

### Sketch

1. ACR capability fields: `side_effect: none | idempotent | once`, `timeout_ms`, `retry` policy.
2. AR: retry only when allowed; `once` → no retry on uncertain timeout, or require `Idempotency-Key` (`correlation_id` + stage_id).
3. Mocks for proof routes: validate required fields; return deterministic ids into next-slot JSON.
4. Compensation stays out-of-band (case system) unless explicit compensate stages are added later.

### Out of scope here

- Pattern 3 allowlist enforcement (policy track).
- Building a general saga engine inside LangGraph.

---

## 5. Runtime conventions as validated DSL

### Why it is needed

Platform teams scale by **publish rules**, not by reading `prefetch.py` / `branch.py`. Tribal conventions (“stage must be named prefetch”; branch keys guessed from `risk` / `tier`) become “works on my seed.” Banks need conventions **documented and linted at publish**, with runtime still fail-closed.

### What v1 does instead

| Convention | Where |
| --- | --- |
| Prefetch stage id must be `"prefetch"` | `prefetch.py` `is_prefetch_stage` |
| Branch choice fields `risk`, `risk_tier`, `branch`, `level`, `tier` (then any matching string) | `branch.py` |
| `llm_role` ∈ `none` / `query_formulation` / `classify` / `synthesis` | `workflow.py` / schema bind |
| Ordered hydrate gated on branch presence | `hydrate.py` |
| Flat schemas for structured LLM bind | `schema.py` |

Eval pin lint covers some catalogue pins; not full workflow semantics.

### When to revive

- Alongside hydrate unification (§1), so the wrong DSL is not baked in.
- Second team authors workflows without AR code reading.
- Nested schemas or multi-branch graphs are requested (may stay rejected — but **explicitly**).

### Sketch

1. In-repo route-contract schema mirrored from the playbook reference.
2. Publish lint: enum roles, prefetch/`type`, `branch_on` JSON path (prefer over field heuristics), diamond-or-reject topology.
3. Prefer `type: prefetch` (or stage flag) over magic id; keep fail-closed at runtime.
4. Extend CataloguePinLint / CI to workflow semantics, not only pins.

### Out of scope here

- Arbitrary DAG workflows or free-form planners in v1 hardening.

---

## 6. Production posture

### Why it is needed

`docker compose up` proves **local contracts**. Banks buy **failure modes**: dual AFD fleets, poison handling, shed load, AZ loss, egress allowlists, secret rotation. Packs (§12 / §17) describe deployment and resilience; the running profile is still stub-auth / stub-Kafka / stub-or-local LLM and one AFD process.

### What v1 does instead

- One Front Door process for chat + jobs; Kafka / IdP stubbed per intent.
- Seed stub LLM special-cases fee / `account_fee_lookup` under `FABRIC_LLM_STUB`.
- Observability track done for local evidence; not multi-AZ DR runbooks as acceptance tests.

### When to revive

- First non-lab environment.
- Need real model gateway without fee-canned stub in the “prod” profile.
- Chaos: kill registry mid-hydrate (must not 202); kill tool mid-`once` POST (no double apply).

### Sketch (phased)

| Phase | Bar |
| --- | --- |
| A | Real LLM path; prod profile disables fee-special stub; stubs only behind `FABRIC_PROFILE=local` |
| B | Two AFD fleets (chat / API); `{runs_topic}` as designed |
| C | Multi-instance AR + open-run rules; Postgres HA; backup/restore runbook |
| D | Egress allowlist AR → ADP / ACR / tools only |
| E | Chaos / poison / shed tests from pack failure tables |

### Out of scope here

- Implementing IdP (separate). Replacing Compose as the local DX.

---

## 7. Publish governance — release train

### Why it is needed

Architecture allows content-driven journeys; banks need **who may publish**, **what gates**, and **rollback = new version / flip active**. Without a train, SQL insert ≈ production product. Eval suites already exist (`agent-fabric-evals`); they should become **merge gates**, not demos.

### What v1 does instead

- Authors edit Flyway seeds (and mocks / utterances) and run local tests.
- `active` on a route version is not a separate controlled promote from “authored.”
- No formal roles: capability publisher ≠ route owner ≠ activator.

### When to revive

- Org-wide or multi-BU adoption.
- Need yank/deprecate of capability versions with lint failure for routes still pinning them.
- Change ticket must separate “published” from “live contest / live jobs pin.”

### Sketch

```text
content PR
  → schema lint (workflow / capability)
  → pin resolve (ADP ↔ ACR)
  → hydrate dry-run (no silent drop)
  → route-quality / intent evals for touched routes
  → side-effect policy present for mutating caps
  → approve + append-only publish
  → activate (separate step / ticket)
```

Roles: **capability publisher** (ACR) ≠ **route owner** (ADP) ≠ **activator**. Related: [versioned route table](#versioned-route-table) for chat contest atomicity.

### Out of scope here

- Full GRC product; human committee process outside the technical gates.

---

## Other suggestions (parked)

Smaller or adjacent items that also matter for platform credibility; revive with the matching section above when possible.

| Suggestion | Why | Ties to |
| --- | --- | --- |
| **Fail loud in Control Plane** | Show pin health / hydrate dry-run errors in ACP so authors see catalogue≠runtime before ops does | §1, §2 |
| **Hydrate snapshot on run status API** | Ops can fetch frozen caps without digging logs | §3 |
| **Asserting mocks for D5 proof routes** | Body-validated tool stubs so dataflow cannot regress silently | §4 |
| **`branch_on` in workflow JSON** | Replace heuristic field list with an explicit path | §5 |
| **Remove / gate fee special-case in seed stub** | Prod profile must not invent fee answers from keyword blobs | §6 |
| **Activate ≠ publish** | Authoring a version must not auto-win chat contest or jobs default | §7, [route table](#versioned-route-table) |
| **Jobs channel on entitle** | Front Door still hardcodes `channel: "web"` on some paths — see [Front Door follow-ups](#front-door-review-follow-ups) | FD parked list |
| **Chat must not resume `job:` freeze keys** | Cross-surface freeze confusion | FD parked list |
| **Model router (later)** | Route/model selection as its own cut; not Pattern work | Separate future cut |
| **Pattern 3 allowlist enforcement** | Catalogue today; runtime ignore — policy track when IdP/PEP lands | Policy (out of this list) |
| **Nested structured output** | Flat schema bind only; document reject or extend `schema.py` deliberately | §5 |
| **Multi-branch / non-diamond graphs** | Reject at publish until topology is specified | §5 |
| **Utterances as catalogue content** | Chat discoverability: Layer ② classpath JSON vs SQL — intent track, not AR | [intent-todo](./intent-todo.md) |

### Stakeholder one-liner

EAF’s architecture is bank-shaped; hardening is **make catalogue executable truth fail-loud, prove pins with a publish train, record evidence, and treat mutating tools as once-only** — not invent more agent patterns.
