# Implementation Plan: Layered intent router (local Fabric)

## Overview

Grow Data Plane decide from v1’s **eligible prune + bind + keyword retrieve** into the [layered classifier](https://jitendersharma.dev/playbooks/agents/intent-router/layered-classifier) pipeline: **eligible → ① rules → ② retrieve → ③ LLM fallback**, with outcomes still `route` / `clarify` / `abstain`. Keep Layer ③ rare. Classify only over eligible `route_id`s. Jobs / named `route_id` stop after ①.

Work this list **after** (or in parallel with the fixture half of) [eval-plan.md](./eval-plan.md): the routing golden set is the gate that lets ②/③ change without rewriting labels. Do not fold these tasks into v1 [todo.md](./todo.md).

**Not in this plan:** Layer ④ safety (injection / PII / veto) as a full input-plane gate; decision-audit store; `route_tables` snapshots ([future-enhancement](./future-enhancement.md#versioned-route-table)); Kafka as a real bus; a second AFD fleet; putting Layer ③ on the Layer ② CPU pool; showing `router_layer` / `route_id` / `confidence` on chat JSON (FR-5).

**Docs map:** [docs/README.md](../README.md). **Behaviour / architecture source:** [layered classifier](https://jitendersharma.dev/playbooks/agents/intent-router/layered-classifier), [agent-plane](../04-architecture/agent-plane.md). Do not reopen locked fabric rules (AFD-only decide, jobs skip ②/③, chat-slim FR-5).

---

## Present vs remaining

What v1 already does in `DecideService` / `CatalogueService` / Front Door freeze, what the playbook still requires, and **how** to close the gap. Task ids live in [intent-todo.md](./intent-todo.md).

### Pipeline (runtime order)

| Playbook layer | Present today | Remaining | How |
| --- | --- | --- | --- |
| **Eligible routes** | Chat: active ∩ `chat_visible` ∩ channel ∩ claims. Empty → `abstain`. Jobs: claims only (hidden routes allowed). | Keep. Jobs must still fail closed on missing claims. Eligible set is the only id universe for ①/②/③. | Do not move this into the classifier. It stays first. I1 makes it an explicit pipeline step. |
| **① Rules** | **Partial bind only:** hint tap / clarify pick / jobs `route_id` skip keywords. Channel is an eligibility filter, not a first-match rule. | Slash / command (`/hr`, “talk to a human”). Topic / event map when a payload names a topic. `router_layer=rules`. Stickiness as a **decide** rule is **not** copied from AFD freeze (see below). | Catalogue-owned rule rows, first match, only if `route_id` is eligible; else `abstain` (no fall-through to ②). I4–I6. |
| **② Classifier** | **Stub:** keyword substring count on `RouteRow.keywords`. Unique hit → `route` at hardcoded `0.91`. Tie → `clarify`. Zero → `abstain`. | Small-model / kNN retrieve on the golden set, &lt; 50 ms, per-route risk bands. Confidence must mean something. | Land eval routing cases first. Replace `keywordRetrieve` behind the same outcomes. Do not train on today’s keyword lists. I7–I9. |
| **③ LLM fallback** | **Absent.** v1 plan: no Layer ③. | Structured JSON over a **fixed eligible `route_id` list**. Rare. Timeout / saturation → `clarify` / `abstain`, never queue behind ②. | Port + hard deadline + default **off**. Only when ② is in the maybe band or the top candidate is high-risk. I10–I12. |
| **④ Safety** | **Absent** on decide. | Injection, PII, veto on **every** path including jobs. `safety_flags`. | **Out of this plan.** Next follow-on after ①–③. Do not bury vetoes inside ②. |
| **Outcomes** | `route` / `clarify` / `abstain`. AFD starts AR only on `route`. Jobs never get `clarify`. | Per-route thresholds. Entity-missing clarify (not a hardcoded fee/transactions prompt). `escalate_human` for events with no user. | Thresholds land with ② (I7). Entity clarify and `escalate_human` stay later unless a seed route needs them. |

### Stickiness, jobs, trace

| Concern | Present today | Remaining | How |
| --- | --- | --- | --- |
| **Session stickiness** | Front Door freeze: live `session_id` **skips decide** and resumes the run. | Playbook ①: read pin → stay on `route_id`, then safety. Follow-ups never re-entitle. | **Keep AFD skip-classify** for a live run. Do not duplicate the pin inside ADP until you need `"yes"` / `"$500"` to re-entitle without a new contest. Document the split (I3). |
| **Jobs / named `route_id`** | `ingress: jobs` + `route_id` → entitle, no keywords, no `clarify`. | Same rule for any payload that already named `route_id` (including a future topic bind). Never ②/③. | Pipeline short-circuit after ① (I1, I5). Topic map is I6, only if the jobs body (or later Kafka) carries `topic`. |
| **Trace fields** | Decide JSON: `intent_label`, `route_id`, `confidence`, `eligible_routes`, `outcome`, `route_version`. Events: outcome, route, channel, eligible count. | `router_layer`, `safety_flags`, `latency_ms`. Decision audit store. | Add `router_layer` + `latency_ms` on decide result and business events now (I2). `safety_flags` waits on ④. Audit store stays out (v1 + this plan). Chat UI still must not see these (FR-5). |

### What we are **not** treating as missing

- Eligible prune by claims and channel — this **is** Layer 0.
- Three outcomes — this **is** the playbook contract.
- Keyword ② — this **is** the v1 stub; replacing it is the ② work, not a bug.
- AFD freeze skip-classify — this **is** session custody, not a decide-layer hole, until continuation re-entitle is a product need.

---

## How (build order)

Runtime order is ① then ② then ③. **Build order is the opposite of “start with an LLM.”**

```text
eval routing golden set (labels survive ②/③ changes)     ← eval E1–E6; do not block I1–I5
    → pipeline + router_layer + jobs stop at ①            ← I1–I3
        → ① slash/command (+ topic only if you have events) ← I4–I6
            → ② risk bands, then retrieve (not keywords)    ← I7–I9
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

```text
# still the catalogue contest — no Compose required for decide unit tests
cd agent-data-plane && mvn test -Dtest=DecideServiceTest,RoutingEval*

# Layer ①
# chat message "/hr" (or seeded command) + jane claims → route via rules, not keywords
# POST jobs with route_id still entitles; missing claims still fail closed

# Layer ②
# "Why was I charged $42?" → route:fee_explain, router_layer=retrieve (not llm)
# close match → clarify; wrong channel → abstain
```

Layer ③ demo is **off** until I12: an ambiguous high-risk utterance either clarifies from ② or, with the flag on, returns `router_layer=llm` within the deadline — or `clarify`/`abstain` on timeout.

---

## Task List

### Phase 0: Pipeline (do this first)

- [ ] Task I1: Split decide into eligible → ① → ② → ③-noop → abstain
- [ ] Task I2: `router_layer` + `latency_ms` on decide result and events
- [ ] Task I3: Document AFD freeze vs decide ① (stickiness split)

### Checkpoint: Pipeline

- [ ] Existing route / clarify / abstain / jobs tests still pass
- [ ] Bind and keyword paths set `router_layer` (`rules` / `retrieve`)
- [ ] Jobs with `route_id` never enter ②
- [ ] Human review before slash rules

### Phase 1: Layer ① rules

- [ ] Task I4: Slash / command rules (catalogue, first match, eligible only)
- [ ] Task I5: Jobs / named `route_id` stay ①-only (tests + `router_layer=rules`)
- [ ] Task I6: Topic / event map (only if jobs body carries `topic`; otherwise skip)

### Checkpoint: Layer ①

- [ ] `/hr` (or seeded command) skips keywords
- [ ] Unknown command that matches no eligible route → `abstain`
- [ ] Jobs still never `clarify`

### Phase 2: Layer ② retrieve

- [ ] Task I7: Per-route risk bands on the current scorer (still keywords OK)
- [ ] Task I8: Replace keywords with retrieve-over-eligible (golden-set / description index)
- [ ] Task I9: ② budget — record `latency_ms`; over budget → `clarify`/`abstain`, do not call ③

### Checkpoint: Layer ②

- [ ] Routing golden set (eval E2–E4) still green, or DecideService adversarial cases if eval not landed
- [ ] Fee ≠ `card_freeze`
- [ ] `router_layer=retrieve` on free-text winners
- [ ] Human review before LLM fallback

### Phase 3: Layer ③ fallback (later, rare)

- [ ] Task I10: Layer ③ port, default off, eligible-ids-only contract
- [ ] Task I11: Bounded executor + timeout → `clarify`/`abstain` (shed, don’t queue)
- [ ] Task I12: Structured JSON fallback when ② is maybe / high-risk (flag on)

### Checkpoint: Layer ③

- [ ] Flag off: behaviour identical to checkpoint ②
- [ ] Flag on + timeout: no hang; `clarify` or `abstain`
- [ ] Jobs / bind still never call ③

### Packaging

- [ ] Task I13: ADP handbook + root README intent notes
- [ ] Task I14: Verification checklist (command, retrieve, ③-off, jobs)

### Checkpoint: Complete (① + ②; ③ optional)

- [ ] All I1–I9 and I13–I14 acceptance criteria in [intent-todo.md](./intent-todo.md) met
- [ ] I10–I12 met or explicitly deferred with flag off
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

- Where do rule rows live? (Default: `dataplane.intent_rules` in ADP, versioned with the catalogue mix, not hardcoded in `DecideService`.)
- Java retrieve stack for I8? (Default: in-process embedding index; pick one library in I8, not a new microservice.)
- How many ② miss cases justify turning ③ on? (Default: measure after I8; keep off for the local demo.)
- Does a jobs `topic` field exist before Kafka? (Default: I6 skipped until the jobs contract has `topic`.)
- Layer ④ as `intent-safety-plan.md` next, or fold a thin veto into decide after I9? (Default: separate plan.)
