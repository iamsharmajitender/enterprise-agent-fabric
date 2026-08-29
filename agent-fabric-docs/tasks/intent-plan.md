# Implementation Plan: Layered intent router (local Fabric)

## Overview

Grow Data Plane decide from v1’s **eligible prune + bind + keyword retrieve** into the [layered classifier](https://jitendersharma.dev/playbooks/agents/intent-router/layered-classifier) pipeline: **eligible → ① rules → ② retrieve → ③ LLM fallback**, with outcomes still `route` / `clarify` / `abstain`. Keep Layer ③ rare. Classify only over eligible `route_id`s. Jobs / named `route_id` stop after ①.

Work this list **after** (or in parallel with the fixture half of) [eval-plan.md](./eval-plan.md): the routing golden set is the gate that lets ②/③ change without rewriting labels. Do not fold these tasks into v1 [todo.md](./todo.md).

**Not in this plan:** Layer ④ safety (injection / PII / veto) as a full input-plane gate; decision-audit store; `route_tables` snapshots ([future-enhancement](./future-enhancement.md#versioned-route-table)); Kafka as a real bus; a second AFD fleet; putting Layer ③ on the Layer ② CPU pool; showing `router_layer` / `route_id` / `confidence` on chat JSON (FR-5).

**Docs map:** [README.md](../README.md). **Behaviour / architecture source:** [layered classifier](https://jitendersharma.dev/playbooks/agents/intent-router/layered-classifier), [agent-plane](../04-architecture/agent-plane.md). Do not reopen locked fabric rules (AFD-only decide, jobs skip ②/③, chat-slim FR-5).

---

## Present vs remaining

What v1 already does in `DecideService` / `CatalogueService` / Front Door freeze, what the playbook still requires, and **how** to close the gap. Task ids live in [intent-todo.md](./intent-todo.md).

### Pipeline (runtime order)

| Playbook layer | Present today | Remaining | How |
| --- | --- | --- | --- |
| **Eligible routes** | Chat: active ∩ `chat_visible` ∩ channel ∩ claims. Empty → `abstain`. Jobs: claims only (hidden routes allowed). | Keep. Jobs must still fail closed on missing claims. Eligible set is the only id universe for ①/②/③. | Do not move this into the classifier. It stays first. I1 makes it an explicit pipeline step. |
| **① Rules** | **Partial bind only:** hint tap / clarify pick / jobs `route_id` skip keywords. Channel is an eligibility filter, not a first-match rule. | Slash / command (`/hr`, “talk to a human”). Topic / event map when a payload names a topic. `router_layer=rules`. Stickiness as a **decide** rule is **not** copied from AFD freeze (see below). | Catalogue-owned rule rows, first match, only if `route_id` is eligible; else `abstain` (no fall-through to ②). I4–I6. |
| **② Classifier** | In-process kNN (token cosine) over labelled seed utterances (`retrieve/utterances.json`), **not** `keywords[]`. Unique hit at `0.91` **routes only if ≥ the row's risk bar**. Close top-2 → `clarify`. Unique high-risk (`high_risk_step_up`, bar `0.95`) → `clarify`. OOD → `abstain`. Budget **50 ms**; at or over → `abstain`, `router_layer=retrieve`, **no ③**. | Small model later. Same bars. | Do not train on today’s keyword lists. |
| **③ LLM fallback** | Port exists. Flag **off**. Bounded 2-thread pool, **500 ms** timeout, queue length 0. Timeout / reject → `abstain`, `router_layer=llm`. Flag off and jobs never submit. | Structured JSON over a **fixed eligible `route_id` list**. Rare. | **Future enhancement:** [I12](./future-enhancement.md#i12-layer-3-llm-fallback) — flag on for ② maybe / high-risk only. |
| **④ Safety** | **Absent** on decide. | Injection, PII, veto on **every** path including jobs. `safety_flags`. | **Out of this plan.** Next follow-on after ①–③. Do not bury vetoes inside ②. |
| **Outcomes** | `route` / `clarify` / `abstain`. Per-route ② bars from `policy_profile` (I7). AFD starts AR only on `route`. Jobs never get `clarify`. | Entity-missing clarify (not a hardcoded fee/transactions prompt). `escalate_human` for events with no user. | Entity clarify and `escalate_human` stay later unless a seed route needs them. |

### Stickiness, jobs, trace

| Concern | Present today | Remaining | How |
| --- | --- | --- | --- |
| **Session stickiness** | Front Door freeze: live `session_id` with `correlation_id` **skips decide** and resumes the run. ADP never reads `frontdoor.freeze`. Documented in the ADP README (I3). | Playbook ①: read pin inside decide, then safety. Follow-ups never re-entitle. | **Out** until a seed case needs `"yes"` / `"$500"` to re-entitle without a new contest. Do not copy freeze into `DecideService` (I4–I12). |
| **Jobs / named `route_id`** | `ingress: jobs` + `route_id` → entitle, no keywords, no `clarify`. | Same rule for any payload that already named `route_id` (including a future topic bind). Never ②/③. | Pipeline short-circuit after ① (I1, I5). Topic map is I6, only if the jobs body (or later Kafka) carries `topic`. |
| **Trace fields** | Decide JSON + events: `router_layer` (`rules` / `retrieve` / `llm`), `latency_ms`. Empty eligible omits `router_layer`. Chat FR-5 still strips these. | `safety_flags`. Decision audit store. | `safety_flags` waits on ④. Audit store stays out. |

### What we are **not** treating as missing

- Eligible prune by claims and channel — this **is** Layer 0.
- Three outcomes — this **is** the playbook contract.
- Keyword ② — **replaced** in I8 by utterance kNN; `keywords[]` may remain on the row unused.
- AFD freeze skip-classify — this **is** session custody, not a decide-layer hole, until continuation re-entitle is a product need.

---

## How (build order)

Runtime order is ① then ② then ③. **Build order is the opposite of “start with an LLM.”**

```text
eval routing golden set (labels survive ②/③ changes)     ← eval E1–E6; do not block I1–I5
    → pipeline + router_layer + jobs stop at ①            ← I1–I3
        → ① slash/command (+ topic only if you have events) ← I4–I6
            → ② retrieve (not keywords), then budget                    ← I8–I9
                → ③ LLM fallback, off by default, shed      ← I10–I12
```

One vertical slice at a time. After each slice, existing `DecideServiceTest` (and later the golden set) still pass: fee utterance → `fee_explain`, never `card_freeze`; jobs still fail closed.

---

## Architecture Decisions

- **Pipeline in `DecideService`, not a new service.** ① and ② stay in-process on decide replicas. Do not HTTP-call another box for retrieve.
- **Eligible is the id universe.** A layer may only assign a `route_id` already in the eligible (chat) or entitled (jobs) set. Otherwise `abstain`.
- **Rules are catalogue data.** First match wins. `router_layer=rules`. Not `if/else` per demo utterance.
- **Jobs stop after ①.** Named `route_id` / topic bind never run ② or ③ and never return `clarify`.
- **② budget &lt; 50 ms.** If it cannot answer, shed to `clarify`/`abstain`. Do not wait on ③.
- **③ is a separate pool.** Locally: bounded executor + hard timeout. Saturate → `clarify`/`abstain`. Default **off** until ②’s miss rate is measured.
- **Golden set encodes intent, not keywords.** Cases are `(utterance, claims, channel) → outcome`. ② may change; labels must not.
- **AFD freeze remains skip-classify** for a live `correlation_id`. Decide-side stickiness is out until a seed case needs re-entitle on `"yes"` / `"$500"`.
- **Chat FR-5 unchanged.** `router_layer` is server-side (decide JSON to AFD, events). Assistant JSON still strips it.
- **④ Safety is the next plan, not a checkbox here.**

---

## Examiner questions (definition of useful)

1. Which routes were eligible for this identity and channel?
2. Which **layer** assigned the outcome (`rules` / `retrieve` / `llm`)?
3. Why this turn routed, clarified, or abstained?
4. Did jobs / named `route_id` skip ② and ③?
5. If ③ is on, did a timeout shed instead of blocking ②?

---

## Demo path (definition of done for ① + ②)

Operator checklist. One place. Tests are enough; a live stack is optional. Layer ② is retrieve over `retrieve/utterances.json`, not `keywords[]`. Layer ③ stays **off**.

### Tests (no Compose)

No local JDK: `docker compose -f agent-fabric-scripts/docker-compose/docker-compose.yml build agent-data-plane` (image build runs `mvn test`). With a JDK: `mvn test` in `agent-data-plane`.

| Check | Passes when |
| --- | --- |
| `/hr` → ① rules | `DecideServiceTest.slashHrRoutesViaRulesWithoutKeywords` — `route` `agent-chat`, `router_layer=rules` |
| `$42` → `fee_explain` ② | `DecideServiceTest.feeUtteranceRoutesToFeeExplain` / golden `chat-fee-charged-42` — `router_layer=retrieve`, not `llm` |
| ③ off | default `fabric.decide.llm.enabled=false`; `flagOffDoesNotCallLlmOnFeeOrJobsOrOod` |
| Jobs missing claims fail closed | `JobsEntitleEvalTest` — `abstain`, never `clarify` |
| FR-5 | `AssistantControllerTest` — assistant JSON has none of `route_id`, `run_id`, `agent_client_id`, `confidence`, `router_layer` |
| Golden set | `RoutingEvalTest` + `JobsEntitleEvalTest` — misroute CI, not the decide hot path |

### Live (optional)

Stack up (`./agent-fabric-scripts/stack/start-app.sh`), then:

```bash
# Pattern 1 shopassist chat (ASK → lookup → policy/billing)
./agent-fabric-scripts/catalogue-seed/run-chat.sh shopassist_case_ask
./agent-fabric-scripts/catalogue-seed/run-chat.sh shopassist_case_ask
```

`/hr` is covered by the unit test above (dummy `agent-chat` uses `hello`, which clarifies). Chat JSON must still omit `router_layer`.

Layer ③ demo stays **off** (I12 deferred). Timeout shed is unit-tested (`hungLlmTimesOutWithoutBlockingDecideBeyondDeadline`); do not turn the flag on in Compose.

---

## Task List

### Phase 0: Pipeline (do this first)

- [x] Task I1: Split decide into eligible → ① → ② → ③-noop → abstain
- [x] Task I2: `router_layer` + `latency_ms` on decide result and events
- [x] Task I3: Document AFD freeze vs decide ① (stickiness split)

### Checkpoint: Pipeline

- [x] Existing route / clarify / abstain / jobs tests still pass
- [x] Bind and keyword paths set `router_layer` (`rules` / `retrieve`)
- [x] Jobs with `route_id` never enter ②
- [ ] Human review before slash rules

### Phase 1: Layer ① rules

- [x] Task I4: Slash / command rules (catalogue, first match, eligible only)
- [x] Task I5: Jobs / named `route_id` stay ①-only (tests + `router_layer=rules`)
- [x] Task I6: Topic / event map (skipped — jobs body has no `topic`; do not invent Kafka)

### Checkpoint: Layer ①

- [x] `/hr` (or seeded command) skips keywords
- [x] Unknown command that matches no eligible route → `abstain`
- [x] Jobs still never `clarify`

### Phase 2: Layer ② retrieve

- [x] Task I7: Per-route risk bands on the current scorer (still keywords OK)
- [x] Task I8: Replace keywords with retrieve-over-eligible (golden-set / description index)
- [x] Task I9: ② budget — record `latency_ms`; over budget → `clarify`/`abstain`, do not call ③

### Checkpoint: Layer ②

- [x] Routing golden set (eval E2–E4) still green, or DecideService adversarial cases if eval not landed
- [x] Fee ≠ `card_freeze`
- [x] `router_layer=retrieve` on free-text winners
- [ ] Human review before LLM fallback

### Phase 3: Layer ③ fallback (later, rare)

- [x] Task I10: Layer ③ port, default off, eligible-ids-only contract
- [x] Task I11: Bounded executor + timeout → `clarify`/`abstain` (shed, don’t queue)
- [x] Task I12: Structured JSON fallback when ② is maybe / high-risk (**deferred** — flag off; reopen when ② miss needs it)

### Checkpoint: Layer ③

- [x] Flag off: behaviour identical to checkpoint ②
- [x] Flag on + timeout: no hang; `clarify` or `abstain`
- [x] Jobs / bind still never call ③

### Packaging

- [x] Task I13: ADP handbook + root README intent notes
- [x] Task I14: Verification checklist (command, retrieve, ③-off, jobs)

### Checkpoint: Complete (① + ②; ③ optional)

- [x] All I1–I9 and I13–I14 acceptance criteria in [intent-todo.md](./intent-todo.md) met
- [x] I10–I12 met or explicitly deferred with flag off (I12 deferred)
- [ ] Human review before Layer ④ safety plan

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| ② trained on today’s keywords | High | Golden set is utterances → outcome; I8 must not copy `keywords[]` as the index |
| ③ on the hot path | High | Default off; separate pool; timeout sheds |
| Slash rules as Java if/else | Med | Catalogue rows (I4); first match; eligible only |
| Stickiness implemented twice | Med | I3: AFD freeze owns live-run resume; ADP does not read freeze |
| Eval golden set not landed | Med | I1–I7 use `DecideServiceTest`; I8 waits on eval E2–E4 or duplicates a minimum adversarial file |
| Chat JSON leaks `router_layer` | High | FR-5 tests already strip it; keep them red if decide fields leak through AFD |
| Scope expands to safety / audit | High | ④ and audit are out; listed in Present vs remaining only |

---

## Open Questions

- Where do rule rows live? **Decided:** `dataplane.intent_rules` (Flyway `V2__intent_rules.sql`). First `sort_order` wins. Not hardcoded in `DecideService`.
- Java retrieve stack for I8? **Decided:** in-process token-cosine kNN over `retrieve/utterances.json`. No extra library, no new microservice.
- How many ② miss cases justify turning ③ on? (Default: measure after I8; keep off for the local demo.)
- Does a jobs `topic` field exist before Kafka? **Skipped (I6).** No `topic` on the jobs decide body. Reopen when the contract grows one; do not invent Kafka.
- Layer ④ as `intent-safety-plan.md` next, or fold a thin veto into decide after I9? (Default: separate plan.)
