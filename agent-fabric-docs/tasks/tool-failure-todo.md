# Task list: Generic tool failure handling (local Fabric)

Plan: [tool-failure-plan.md](./tool-failure-plan.md). Docs map: [README.md](../README.md). Related: [future-enhancement §4 side-effect invoke](./future-enhancement.md#4-side-effect-tools--invoke-policy), [audit-todo](./audit-todo.md) (optional later emit).

**Execution order:**

1. **Contract** — TF1. Envelope, categories, soft empty.
2. **Classify** — TF2. Invoker normalizes HTTP + body → `ToolOutcome`.
3. **Policy** — TF3. Generic action table (human checkpoint).
4. **Runtime wire** — TF4–TF5. Pattern 1 then Pattern 2/3.
5. **Proof** — TF6–TF7. Mocks + demo path.
6. **Docs** — TF8.

v1 fabric tasks remain in [todo.md](./todo.md); dataflow / audit / intent / eval lists do not replace this track.

Dummy jobs returning `completed` without envelope-aware failure proofs is **not** acceptance.

---

## 0. Contract

## Task TF1: Freeze tool outcome envelope + semantics

**Description:** Document the shared `ToolOutcome` contract (ok, errorCategory, isRetryable, code, customerMessage, developerMessage, data, message) and mapping rules for soft empty vs business/permission vs technical. Add checked JSON examples under `agent-fabric-docs/05-reference/`.

**Acceptance criteria:**
- [ ] Field table matches [tool-failure-plan.md](./tool-failure-plan.md) envelope section
- [ ] Examples: success, soft empty, `business` deny, `permission`, `validation`, `transient`, `system`
- [ ] Explicit: Runtime policy keys only on category + flags — never on domain `code` strings
- [ ] Cross-link to side-effect §4 for mutate retry gating

**Verification:**
- [ ] Manual: a new session can author a tool response by copying an example
- [ ] Plan open questions listed but not silently decided in the schema file

**Dependencies:** None

**Files likely touched:**
- `agent-fabric-docs/05-reference/tool-outcome-envelope.json` (and/or examples)
- `agent-fabric-docs/tasks/tool-failure-plan.md` (link only if needed)

**Estimated scope:** Small

---

## Checkpoint: Contract

- [ ] Human agrees soft empty ≠ business deny
- [ ] Categories set is closed for v1 of this track (`validation` | `permission` | `business` | `transient` | `system`)

---

## 1. Classify

## Task TF2: Normalize HTTP + body in `ToolInvoker`

**Description:** Replace bare `raise_for_status` success-only path with normalization to `ToolOutcome`. Map transport/HTTP failures to categories; detect `isError` / `outcome=denied` / agreed soft-empty shapes on 2xx bodies. Uncaught → `system`.

**Acceptance criteria:**
- [ ] `HttpToolClient.call` (or thin wrapper) returns or raises a single structured outcome type used by the graph
- [ ] Unit tests cover: 503→transient, 400→validation (or system per TF1 map), 2xx+`isError` business, soft empty, invalid JSON
- [ ] Spans still record `http.status_code`; errors recorded without dumping secrets into attributes
- [ ] No domain-specific `code` handling in the invoker

**Verification:**
- [ ] `uv run pytest` (or project equivalent) passes new invoker/classifier tests
- [ ] Existing happy-path tool invokes still return usable `data` for slot merge

**Dependencies:** TF1

**Files likely touched:**
- `agent-runtime/app/tools/invoker.py`
- `agent-runtime/app/tools/outcome.py` (new) or similar
- `agent-runtime/tests/test_tool_outcome.py` (new)

**Estimated scope:** Medium

---

## 2. Policy

## Task TF3: Generic policy table + Action (human checkpoint)

**Description:** Pure module: `(ToolOutcome, context) → Action` where Action ∈ `retry` | `observe` | `escalate` | `fail_run` | `continue`. Context may include pattern/autonomy, retry count, and optional capability `side_effect` when present. **No** refund/KYC branches. Resolve plan open questions in writing on the plan doc.

**Acceptance criteria:**
- [ ] Default action table implemented as data + tests (table-driven)
- [ ] Open questions in [tool-failure-plan.md](./tool-failure-plan.md) answered (escalate convention, 404-as-empty, mutate retry default)
- [ ] Escalate action specifies how to select an escalation tool (tag / fallback / none → fail_run) without domain names
- [ ] `business` + `permission` never select `retry` for the same invocation args

**Verification:**
- [ ] Unit tests for each category × retryable cell
- [ ] Human sign-off on escalate convention before TF4

**Dependencies:** TF1 (TF2 can proceed in parallel on classifier shape)

**Files likely touched:**
- `agent-runtime/app/tools/policy.py` (new)
- `agent-runtime/tests/test_tool_policy.py` (new)
- `agent-fabric-docs/tasks/tool-failure-plan.md` (open questions → decisions)

**Estimated scope:** Medium

---

## Checkpoint: Policy

- [ ] Escalate convention locked
- [ ] Mutate + `isRetryable` default locked until §4
- [ ] Review: zero domain strings in `policy.py`

---

## 3. Runtime wire

## Task TF4: Pattern 1 agent loop consumes Outcome/Action

**Description:** Replace stringly `"tool error (…): {exc}"` continue path with structured notes from `customerMessage`/`code`, apply retry only when Action says so, and invoke escalation capability when Action is `escalate` and a tagged tool exists.

**Acceptance criteria:**
- [ ] Pattern 1 does not blind-retry `business` / `permission`
- [ ] LLM-facing notes never include stack traces or `developerMessage` by default
- [ ] Retry respects bounded N from policy
- [ ] Tests: mock invoker returns business deny → observe/escalate path; transient → retry then stop

**Verification:**
- [ ] `tests/test_graph.py` (or new) covers deny vs transient
- [ ] Existing Pattern 1 happy path still completes

**Dependencies:** TF2, TF3

**Files likely touched:**
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/tests/test_graph.py`

**Estimated scope:** Medium

---

## Task TF5: Pattern 2/3 linear stages use the same path

**Description:** Domain HTTP stages in linear/branch workflows classify through the same invoker + policy. Default: `business`/`permission`/`system` → `fail_run` (or escalate if workflow/manifest provides it); soft empty fails closed when next schema requires the entity.

**Acceptance criteria:**
- [ ] One shared helper used by stage runner and Pattern 1 (no duplicated category switches)
- [ ] Failed run reason code uses envelope `code` or category — not raw exception text only
- [ ] Checkpoint resume behaviour documented relative to failed tool stage (no silent skip)

**Verification:**
- [ ] Unit or graph test: linear stage business deny → failed (or escalate) per TF3
- [ ] Soft empty + required next field → fail closed

**Dependencies:** TF4

**Files likely touched:**
- `agent-runtime/app/graph/workflow.py`
- `agent-runtime/app/core/agent_core.py` (if stage failure surfaces here)
- `agent-runtime/tests/**`

**Estimated scope:** Medium

---

## Checkpoint: Runtime

- [ ] Pattern 1 + one Pattern 2 path share classifier/policy
- [ ] `rg -n 'REFUND|refund_policy|KYC' agent-runtime/app` shows no new domain failure branches

---

## 4. Proof

## Task TF6: Mocks emit envelope examples

**Description:** Teach `agent-fabric-mocks` at least three behaviours: soft empty, business deny (`isRetryable: false`), transient/503 (or JSON transient). Prefer dedicated proof paths/query flags so `--all` smoke is unchanged unless opted in.

**Acceptance criteria:**
- [ ] Documented how to trigger each behaviour (path, header, or body flag)
- [ ] Responses match TF1 examples
- [ ] No requirement that every canned tool suddenly speaks the envelope (gradual)

**Verification:**
- [ ] curl/script hits each proof behaviour
- [ ] Classifier tests can optionally hit mocks in compose (nice-to-have, not required)

**Dependencies:** TF1

**Files likely touched:**
- `agent-fabric-mocks/tools/server.py` and/or catalog entries
- `agent-fabric-mocks/tools/README.md` (or existing mocks README)

**Estimated scope:** Small–Medium

---

## Task TF7: Demo path — deny then escalate (generic)

**Description:** One scripted or test demo: tool business deny → policy escalate → escalation tool (or tagged mock) called with `code`/`developerMessage` summary. AR must not name the domain beyond tool ids in the manifest.

**Acceptance criteria:**
- [ ] Demo documented in plan or runtime README
- [ ] Asserts: no HTTP retry on deny; escalation invoked once when configured
- [ ] Works with Pattern 1 or a tiny proof workflow — pick one and stick to it

**Verification:**
- [ ] Automated test or `agent-fabric-scripts` script with clear pass/fail
- [ ] Dummy `--all` not used as the proof

**Dependencies:** TF4, TF6 (TF5 if linear demo chosen)

**Files likely touched:**
- `agent-runtime/tests/**` or `agent-fabric-scripts/stack/**`
- `agent-fabric-docs/tasks/tool-failure-plan.md` (demo path checkboxes)

**Estimated scope:** Medium

---

## 5. Docs

## Task TF8: Runtime docs + status + optional audit note

**Description:** Update agent-runtime README / understand-status so operators know tool outcomes are classified generically. Note optional future audit `stage.tool_outcome`. Link §4 for mutate retries.

**Acceptance criteria:**
- [ ] README section: categories, soft empty, policy actions, escalate convention
- [ ] [status.md](../02-understand/status.md) or equivalent notes catalogue vs runtime behaviour for tool failures
- [ ] [future-enhancement.md](./future-enhancement.md) points at this track as active for failure envelope; §4 remains side-effect fields
- [ ] Plan verification checklist updated

**Verification:**
- [ ] Links from [README.md](../README.md) reader path resolve
- [ ] Human can follow demo without reading chat history

**Dependencies:** TF7

**Files likely touched:**
- `agent-fabric-runtime/README.md`
- `agent-fabric-docs/02-understand/status.md`
- `agent-fabric-docs/tasks/future-enhancement.md`
- `agent-fabric-docs/README.md` (if not already linked)

**Estimated scope:** Small

---

## Checkpoint: Track complete

- [ ] TF1–TF8 acceptance criteria checked
- [ ] Demo path green
- [ ] Human review: Runtime remains domain-generic
- [ ] Add Done line under **Active follow-on** / **Done** in [future-enhancement.md](./future-enhancement.md) when signed off

---

## Later (parked — not TF blockers)

| Item | Why later |
| --- | --- |
| ACR `side_effect` / retry fields | [§4](./future-enhancement.md#4-side-effect-tools--invoke-policy) |
| AADP `stage.tool_outcome` events | Audit Phase B-style; after envelope stable |
| Publish lint that example tool responses match envelope | Nice after mocks prove value |
| Compensation / saga stages | Out of plan |
