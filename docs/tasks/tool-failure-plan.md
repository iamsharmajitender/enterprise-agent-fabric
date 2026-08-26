# Implementation Plan: Generic tool failure handling (business + technical)

## Overview

Give **every domain tool** one result contract so Agent Runtime can react the same way for refunds, freezes, KYC, and mocks — without baking domain rules into the graph.

Today Runtime treats most tool problems as raw exceptions: `HttpToolClient` raises on non-2xx; Pattern 1 catches `RuntimeError`, appends `"tool error (…)"` to `notes`, and continues. There is **no** shared distinction between:

- **Technical** failures (timeout, 5xx, bad args) vs **business** denies (policy / eligibility / ownership)
- **Retryable** vs **non-retryable**
- Soft **empty** (not found) vs hard **deny**

That makes the loop either too retry-happy (policy denies) or too opaque (stack-ish notes). Banks need a **generic classifier + policy table** in AR, and **domain-specific messages/codes** only at the tool boundary.

**Task list:** [tool-failure-todo.md](./tool-failure-todo.md). **Docs map:** [docs/README.md](../README.md).

**Related (do not fold blindly):**

| Track | Relationship |
| --- | --- |
| [future-enhancement §4 — side-effect invoke policy](./future-enhancement.md#4-side-effect-tools--invoke-policy) | Caps **when** HTTP retry is allowed (`once` / `idempotent`). This plan owns **how** failures are classified and which **next action** runs after classify. |
| [audit-plan](./audit-plan.md) | Optional later: emit `stage.tool_outcome` digests (`code`, category, retry count) — not a Phase 1 blocker. |
| [dataflow-plan](./dataflow-plan.md) | Slots/merge stay as-is; failure envelope is orthogonal to successful hop JSON. |

**Not in this plan:** Saga/compensation engine; LLM-as-judge of tool output; per-route hardcoded “if refund then escalate”; changing chat FR-5 wire JSON; Shared Memory; inventing new capability `kind`s.

---

## Present vs remaining

| Concern | Runtime / mocks today | This plan |
| --- | --- | --- |
| HTTP non-2xx | `raise_for_status` → exception | Map to envelope (`transient` / `system` / `validation`) |
| Tool JSON body with policy deny | Treated as success if 200 | Detect `isError` / `outcome=denied` → `business` / `permission` |
| Soft not-found | Ad hoc / mock-dependent | Convention: `isError=false` + null entity + `message` |
| Pattern 1 tool exception | String note, continue loop | Classify → policy action (retry / observe / escalate / stop) |
| Pattern 2/3 linear stage fail | Fail run (typical) | Same classifier; policy may fail-closed or `waiting` |
| Domain knowledge in AR | None (good) — but also no generic policy | Keep AR domain-free; policy keyed only by category + flags |
| Mutating tool retry safety | No `side_effect` gate | Defer field to §4; until then: **no blind retry** on uncertain mutate unless `isRetryable` and capability allows |

---

## Architecture decisions (accepted for this track)

### 1. One envelope for all tools

Every domain HTTP tool result that Runtime consumes is normalized to:

```text
ToolOutcome {
  ok: boolean                 // false ⇒ classified failure (tech or business)
  errorCategory?:             // validation | permission | business | transient | system
  isRetryable: boolean        // default false when ok=false
  code?: string               // stable machine id, domain-owned (e.g. REFUND_OUTSIDE_WINDOW)
  customerMessage?: string    // safe for user / LLM rephrase
  developerMessage?: string   // logs / escalation summary only
  data?: object | null        // success payload or soft-empty null
  message?: string            // soft-empty explanation when ok=true && data==null
}
```

**Wire options tools may emit** (adapter accepts both):

| Tool returns | Normalized |
| --- | --- |
| 2xx + business body without error flags | `ok=true`, `data=body` (or schema subset already used for slots) |
| 2xx + `{ isError: true, errorCategory, … }` | `ok=false`, copy fields |
| 2xx + `{ eligible: false }` / `{ outcome: "denied", … }` | `ok=false`, `errorCategory=business` (mapper rules frozen in TF1) |
| Soft miss `{ customer: null, message }` with `isError: false` | `ok=true`, `data=null`, `message` |
| HTTP 4xx/5xx / timeout / transport error | `ok=false`, category from status map; body ignored or merged if JSON envelope present |

Tools **do not** need identical success shapes. They **do** need either a success object or a recognizable failure/empty convention.

### 2. Soft empty ≠ business deny

| Case | `ok` | Category | Agent/runtime |
| --- | --- | --- | --- |
| Email not in CRM | true | — | Clarify / try another id |
| Order unknown | true | — | Clarify |
| Order owned by someone else | false | `permission` | Explain; do not retry same args; escalate if policy says |
| Outside return window | false | `business` | Explain; escalate / alternate; **never** retry same check expecting a different answer |
| Amount ≤ 0 | false | `validation` | Repair args / ask user |
| 503 / timeout | false | `transient` | Retry only if `isRetryable` **and** side-effect policy allows |

### 3. Runtime stays generic — policy table, not domain `if`s

AR **must not** contain `if code == REFUND_OUTSIDE_WINDOW`. It only reads:

```text
(errorCategory, isRetryable, side_effect?, autonomy_mode / pattern)
  → Action
```

**Default action table (v1 of this track):**

| Category | `isRetryable` | Default action |
| --- | --- | --- |
| `transient` | true | Retry with bounded backoff (cap N); then `fail_run` or `escalate` |
| `transient` | false | `fail_run` or observe (Pattern 1) per route risk |
| `validation` | false | Pattern 1: observe + continue (model repairs). Pattern 2/3: `fail_run` |
| `permission` | false | Explain via `customerMessage`; optional escalate capability; no same-args retry |
| `business` | false | Same as permission (explain + optional escalate / alternate tool if in manifest) |
| `system` | false | `fail_run` (high risk) or observe once (Pattern 1 chat) then stop |

**Escalate** means: if the hydrated manifest includes a designated escalation capability (convention: tool id / tag `escalation` **or** route `fallback` already on catalogue), invoke it with allowlisted args from `goal` ∪ slots ∪ `{ reason: code, summary: developerMessage }`. If none exists → set run `failed` or `waiting` with reason code — **do not** invent a human ticket API inside AR.

### 4. Where classification lives

```text
Domain tool / mock
    → HTTP status + JSON body
        → ToolInvoker / adapter (normalize → ToolOutcome)   ← classification
            → Graph stage / agent loop (apply Action)       ← policy only
```

- **Tools** own domain codes and messages.
- **Invoker** owns HTTP→envelope and unwrap of `isError` bodies.
- **Graph** owns retry counters, notes projection, escalate/fail — still domain-free.

Uncaught exceptions in the adapter become `system` / `isRetryable=false`.

### 5. Pattern-specific behaviour (same classifier)

| Pattern | On `business` / `permission` | On `transient` retry exhausted | On soft empty |
| --- | --- | --- | --- |
| **1** (LLM loop) | Append structured note (`customerMessage` + `code`); do not re-CALL same tool with same args in the same step; model may escalate tool or DONE | Structured note; DONE or escalate | Note + continue |
| **2/3** (linear / branch) | Prefer `fail_run` or `waiting` + escalate stage if workflow declares one; do not silently skip | `fail_run` | Fail closed if next `input_schema` requires the entity |

Checkpoint resume (`loop=checkpoint`) must not replay a **successful** mutate; interacts with §4 `once`.

### 6. Keeping Runtime generic — hard rules

1. **No domain strings in policy code** — only categories + booleans + optional capability tags.
2. **No “refund agent” branch** in `workflow.py` — escalation is a **manifest tool** or catalogue `fallback`, not Python.
3. **Customer vs developer messages** — LLM / chat may see `customerMessage`; tickets/logs get `developerMessage`; never put stack traces in `notes` for the model.
4. **Idempotency** — retries for `transient` on mutating tools require §4 fields; until then default **no retry** when capability is known mutating (or when unsure).
5. **Mocks teach the contract** — at least one proof tool returns business deny + one transient; Pattern 1 demo shows escalate without AR knowing “refund”.

### Rejected (for now)

| Alternative | Why not first |
| --- | --- |
| Throw typed Java/Python exceptions per domain | Crosses HTTP boundary poorly; LLM loop needs JSON-shaped outcomes |
| Only HTTP status codes | Business denies are often **200 + body** |
| LLM free-reads any JSON and “figures out” retry | Non-deterministic; unsafe on money movers |
| Per-route custom failure DSLs on catalogue day one | Over-design; category table covers 95% |
| Fold side-effect ACR fields into TF1 | Separate concern; link §4 and gate retries |

---

## Build order

```text
TF1 freeze envelope + category semantics + soft-empty rules (docs/05-reference)
    → TF2 HTTP/status + body classifier in ToolInvoker (unit tests)
        → TF3 policy table + Action type (pure module, no domain)
            → TF4 Pattern 1 loop uses Outcome/Action (replace stringly tool error)
                → TF5 Pattern 2/3 linear stages use same path
                    → TF6 mocks: business deny + transient + soft empty proof
                        → TF7 one seed/demo path (escalate capability optional)
                            → TF8 docs (runtime README + status) + optional audit hook note
```

Human checkpoint after **TF3**: confirm default action table and escalate convention (manifest tag vs route fallback) before wiring the loop.

---

## Demo path (definition of done)

1. Mock tool A returns soft empty → run continues / clarifies (Pattern 1 note), not `failed` solely for empty.
2. Mock tool B returns `errorCategory=business`, `isRetryable=false` → **no** HTTP retry; note or escalate; AR logs `code` only.
3. Mock tool C returns transient / 503 with `isRetryable=true` on a **non-mutating** capability → bounded retry then structured failure.
4. Same classifier used from Pattern 1 and one linear Pattern 2 stage — no refund-specific Python.

Dummy `--all` green without envelope-aware mocks is **not** acceptance.

---

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Tools keep returning free-form 200 success for denies | Med | Classifier docs + mock proofs; lint later on ACR examples |
| Blind retry doubles money move | High | Default no retry on mutate; align with §4 before enabling transient retry on POST |
| Escalate convention bikeshed | Med | Lock in TF3 human checkpoint: prefer capability tag `escalation` |
| Notes leak developerMessage | Med | Explicit projection helper for LLM-facing notes |
| Overlap with audit stage digests | Low | TF8 documents optional `stage.tool_outcome`; implement on audit Phase B if needed |

---

## Open questions (resolve in TF3 checkpoint)

1. Escalate: **capability tag** `escalation` vs catalogue **`fallback`** route vs run status `waiting` only?
2. Soft empty: require `isError: false` + null field, or also accept HTTP 404 as soft empty for GETs?
3. Until §4 lands: treat all non-GET invokes as **non-retryable** even when body says `isRetryable: true`?

---

## Verification checklist (track sign-off)

- [ ] Envelope schema + examples under `docs/05-reference/`
- [ ] Unit tests: status map + `isError` body + soft empty
- [ ] Unit tests: policy table actions (no domain codes)
- [ ] Pattern 1: business deny does not re-invoke same tool same args automatically
- [ ] Pattern 2 stage: business deny fail-closed or escalate per TF3 decision
- [ ] Mock proof + short README section on tool outcomes
- [ ] Human review: Runtime still has zero refund/KYC branches
