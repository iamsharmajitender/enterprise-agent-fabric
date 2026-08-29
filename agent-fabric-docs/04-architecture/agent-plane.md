# Agent Plane — solution architecture and design

**Box:** Agent Control Plane (ACP) + Agent Data Plane  
**Parent:** [Enterprise Agent Fabric](./narrative/enterprise-agent-fabric.mdx) · **Behaviour source:** [agent-plane.mdx](./narrative/agent-plane.mdx)  
**Status:** Draft · **Date:** 2026-08-20  
**This binary:** [02-understand/status.md](../02-understand/status.md). This pack may be ahead of code.  
**Audience:** CTO / chief architect (solution on a page); platform engineer (design)

One plane per trust domain. Two boxes inside it. Catalogue plus classify. Does **not** pin. Does **not** start AR. Does **not** mint `correlation_id`.

---

## 1. Solution on a page

### Business problem

Every UI and partner API guesses the agent (`if/else`, a second chatbot, a hard-coded URL). Entitlements fragment. There is no single eval surface for misroutes, no shared clarify/abstain/safety, and no versioned catalogue. High-risk routes get side doors. Operators cannot show why a turn routed.

### Key requirements

| ID | Requirement (this box) |
| --- | --- |
| FR-1 | Only the two AFDs call decide. AR may **GET** the catalogue row at the pinned version. Plane is not a public URL. |
| FR-2 | Decide = active table ∩ `required_claims` ∩ channel. Explicit `route_id` still looks up, entitles, and records. |
| FR-3 | Outcomes: `route`, `clarify`, `abstain`. Only `route` starts AR (and AFD does the start). Jobs with no user fail closed or `escalate_human`. |
| FR-5 | Chat/UI never sees `route_id`, `confidence`, or `router_layer`. Decision record is server-side. |
| FR-6 / FR-7 | Eligible chips are chat-visible only. Jobs skip Layer ② / ③, not eligible, safety, or the decision record. |

Decide path: Layer ② &lt; 50 ms. Decide must not wait on a 12-step loop or on audit commit. Catalogue unreadable: fail closed.

### Architecture

![AFD calls the Data Plane to decide. The Data Plane classifies against the versioned catalogue. ACP writes the decision audit asynchronously. Neither box starts AR.](./diagrams/plane-solution.svg)

[Editorial diagram](./diagrams/plane-solution.html)

AFD calls classify, then freezes and starts. This plane does not call AR.

### Key technology decisions

| Choice | Why |
| --- | --- |
| ACP ≠ Data Plane | Control/audit can lag. Classify must fail closed and stay on the hot path. |
| Plane does not pin or start | Pin sits on AFD (channel session). Start sits on AR. Decide SLO is classify, not work. |
| Versioned in-memory catalogue | Eligible set ∩ claims ∩ channel must be local. Origin QPS on every turn does not hold. |
| Cheap layers first | Layer ① bind, Layer ② retrieve (&lt;50 ms), Layer ③ only if needed. Safety on every path. |
| Async decision audit | Decide SLO does not include "audit committed." Exam trail may lag. |
| Layer ③ on a separate pool | If saturated: `clarify` / `abstain`, not a slower ACP. |
| Jobs still hit Plane ① | Explicit `route_id` is not a skip of entitle + record. |

### Expected outcomes

- One ingress decision for a shared experience.
- One versioned catalogue and one eval surface (golden set / CI).
- Operators can show eligible set, `router_layer`, outcome, and `route_table_version`.
- A down AR does not stop new turns. A down catalogue stops starts (correct).

### This box owns / does not own

| Box | Owns | Does not own | If it dies |
| --- | --- | --- | --- |
| ACP | Policy, versions, decision audit | Pin, start, loop, AFD hot-path classify | Audit lags; in-flight runs continue |
| Agent Data Plane | Eligible set, classify, route/workflow catalogue | Pin, start, loop | Classify fails closed |
| Decision audit | Async `router_layer`, `outcome`, `eligible_routes` | Chat transcript | Decide still succeeds |

**Three routers — do not collapse**

| Router | Question | Who calls it |
| --- | --- | --- |
| Agent Data Plane | Which workflow / manifest / app? | AFD (classify). AR (row at pin, not classify) |
| Agent planner | Which tool / step next? | AR |
| Model router | Which LLM endpoint? | AR |

---

## 2. Context

Callers are Chat AFD, API AFD, and AR (catalogue row at the pinned version only). Evals talk to ACP. Channels have no URL here.

| Actor | Relationship |
| --- | --- |
| Chat AFD | Message + claims + `session_id`. May send `route_id` on hint tap / clarify pick (Layer ①). |
| API AFD | Explicit `route_id` + claims. Never receives `clarify`. |
| AR | `GET` catalogue row **pointers** at pinned `route_table_version` after start. Does not classify. Does not load `active`. |
| Platform / domain teams | Author versioned catalogue rows (`agent_client_id`, `activation_target`, manifest pointer). |
| Agent evals | Golden set and adversarial cases against this catalogue. CI gate. |
| Channels / browsers | **No relationship.** Not a public URL. |

Frozen route/session is on AFD. Run pin is on AR. Capability versions are on the [Registry](./agent-capability-registry.md) (same Agent Plane band).

---

## 3. Container / component architecture

Decide replicas hold the catalogue in memory, then Layer ① → ②, with Layer ③ on a separate pool. Safety runs on every path. ACP publishes the decision record asynchronously. Detail: [solution diagram](./diagrams/plane-solution.html).

| Component | Responsibility |
| --- | --- |
| Decide | Hot path. In-memory catalogue ∩ claims ∩ channel, then layers, then safety. Returns `route` / `clarify` / `abstain`. |
| Eligible | Chat-visible ∩ claims ∩ channel. Event-only rows omitted. Used for chips, not start. |
| Catalogue row API | Pointers at a **pinned** version: `activation_target`, manifest, policy, model, memory, `agent_client_id`. Not the authored blob the UI must never see. |
| Layer ① | Bind: hint tap, clarify pick, jobs `route_id`, topic bind. |
| Layer ② | Retrieve. Budget &lt; 50 ms. Scale on this CPU. |
| Layer ③ | Separate pool. Rare. Saturate → `clarify` / `abstain`. |
| Safety | Every path, including jobs. |
| Audit publisher | Async. Full trace. Not on the decide clock. |

**Hot path.** Whole eligible set in replica memory. Unreadable: fail closed. No session affinity. AFD is the only decide caller.

Classification runs only over eligible routes. Pipeline detail: layered classifier playbook (not duplicated here).

---

## 4. Deployment architecture

```text
                    No public ingress
                            │
                    Mesh / ClusterIP only
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
     Decide + eligible                Catalogue row
     (stateless, 3 AZ)                (read replicas)
              │
              ├── Layer ② pool (HPA on CPU / latency)
              └── Layer ③ pool (separate HPA; shed, don't queue)
              │
     ACP audit workers  →  audit store (async)
     Catalogue origin   →  push versioned snapshot to replicas
```

| Concern | Stance |
| --- | --- |
| Ingress | None from channels. AFD and AR only, private network / mesh mTLS. |
| Egress | Audit store, eval hooks, events. Does **not** egress to AR start. |
| Scale Chat AFD, API AFD, and this plane as **three fleets**. | Decide RPS + Layer ② latency. Does not grow with SSE sockets or loop length. |
| Catalogue rollout | Version bump, not turn rate. Replicas load the new table; old pins keep old versions. |
| Failover | Lose decide replicas: classify fails closed (correct). Lose audit workers: decide still succeeds. |
| Isolation | Do not share an autoscaler with AFD or AR. Do not put Layer ③ on the Layer ② pool. |

Working order of saturation at hundreds of turns/s: (1) UI SSE on Chat AFD, (2) Layer ② CPU for free-text chat, (3) start-ack to a hot AR, (4) freeze KV, (5) Layer ③ — only if you put it on the hot path. Do not.

---

## 5. API design

Module or internal RPC. Not OpenAPI for channels. Not API keys for partners.

### Auth

Workload identity of Chat AFD, API AFD, or AR. Reject any other caller. AR is allowed **catalogue row GET** only, not decide.

### Endpoints

| Method | Path | Caller / when | Response |
| --- | --- | --- | --- |
| `POST` | `/v1/intent/decide` | Every new decide. Chat: message + claims + `session_id`. Jobs: `route_id` + claims. Hint/clarify: `route_id` as Layer ① | `route`, `clarify`, or `abstain`. Writes decision record async |
| `GET` | `/v1/intent/eligible` | UI hints | Chat-visible ∩ claims ∩ channel |
| `GET` | `/v1/catalog/routes/{route_id}` | After `outcome=route` only. Query `route_table_version` | Row **pointers** at that version |
| `GET` | `/v1/catalog/corpora` | NAR / ACP. Query `include=all` for drafts | Published search endpoints by default |
| `GET` | `/v1/catalog/corpora/{corpus_id}` | NAR looks up each `retrieval.scope` id, then POSTs `url` | One row per index. Two ids → two lookups |

Chat with a frozen route/session and a continuation **does not** call decide.

Decide request (chat vs jobs):

```json
{
  "ingress": "chat",
  "channel": "web",
  "session_id": "chat-11111111-1111-4111-8111-111111111111",
  "message": "Why was I charged $42?",
  "route_id": null,
  "claims": { "sub": "jane", "emts": { "accounts:read": true } }
}
```

```json
{
  "ingress": "jobs",
  "channel": "api",
  "route_id": "contract_review",
  "claims": { "sub": "svc-legal-jobs", "emts": { "legal:msa_review": true } }
}
```

Decide response — `route` (commits filled):

```json
{
  "outcome": "route",
  "intent_label": "fee_explain",
  "route_id": "fee_explain",
  "route_table_version": "2026.08.1",
  "confidence": 0.91,
  "eligible_routes": ["fee_explain", "account_history", "policy_qa"]
}
```

Decide response — `clarify` (commits null; jobs never get this):

```json
{
  "outcome": "clarify",
  "intent_label": null,
  "route_id": null,
  "route_table_version": null,
  "confidence": null,
  "clarify_prompt": "Did you want a fee explanation or recent transactions?",
  "candidates": [
    { "intent_label": "fee_explain", "route_id": "fee_explain", "confidence": 0.62, "label": "Explain a fee" },
    { "intent_label": "account_history", "route_id": "account_history", "confidence": 0.58, "label": "Show recent transactions" }
  ],
  "eligible_routes": ["fee_explain", "account_history", "policy_qa"]
}
```

AFD sees `outcome` and, on `route` only, `route_id`, `intent_label`, `route_table_version`, `confidence`. The **decision record** (ops/eval) also has `router_layer`, `eligible_routes`, `safety_flags`, `latency_ms`.

### Errors, idempotency, rate limits

| Condition | Behaviour |
| --- | --- |
| Catalogue unreadable / empty snapshot | Fail closed. Do not return a stale `active` guess. |
| Unknown `route_id` (jobs) | `abstain` or equivalent deny. Record it. |
| Missing claims | Empty eligible. `abstain`. Jobs: fail closed. |
| Layer ③ timeout / saturation | `clarify` or `abstain`. Do not enqueue behind Layer ②. |
| Duplicate decide | Not a start. Fine to re-decide; audit gets two rows. AFD must not start twice (that is AR idempotency). |
| Rate limit | Per AFD fleet identity. Prefer shed to `clarify`/`abstain` over 429 on chat if eligible set is non-empty and Layer ③ is the bottleneck. |

---

## 6. Data architecture

### Route / workflow catalogue

Versioned rows. Includes `agent_client_id` per row. Field dictionary lives in the route-contract playbook; this pack records what the plane must store.

| Field | Why |
| --- | --- |
| `route_id` | Stable name. |
| `route_table_version` | Pin unit. |
| `required_claims` | Entitlement. Not per-user rows in this table. |
| `channels` / `chat_visible` | Eligible vs chips vs event-only. |
| `activation_target` | Which AR. Omit = shared runtime. |
| `agent_client_id` | Which robot. |
| `tool_manifest` + version | Pointer. No inlined `tools[]`. |
| `policy_profile` / `model_profile` | Pointers AR copies into the run pin. |
| `autonomy_mode` | Who decides the next step: `0` single inference, `1` autonomous, `2` deterministic, `3` guided. |


**Indexes:** `(route_id, route_table_version)` unique. Replica snapshot is the whole active table for a version. Decision audit: `(session_id, at)`, `(route_id, at)`, `outcome`.

**Consistency:** Catalogue reads at a named version (pinned) are repeatable. Decide against **active** for new turns. AR and AFD must not re-read `active` after pin.

**Retention:** Catalogue versions retained for replay / exam (policy). Decision records retained per audit policy. Not the chat transcript.

**Partitioning:** Audit by time. Catalogue is small (working target: 5–8 chat-visible routes plus a few event-only rows).

---

## 7. Event / messaging design

Decide is synchronous RPC. Audit is the messaging path.

| Topic | Partition key | Producer | Consumer | Semantics |
| --- | --- | --- | --- | --- |
| `agent.decision.recorded` (working name) | `session_id` | ACP audit publisher | Audit store, eval, observability | At-least-once. Decide already returned |
| Catalogue version published | `route_table_version` | Control pipeline | Decide replicas | Fan-out snapshot. Not a turn event |

| Concern | Stance |
| --- | --- |
| Ordering | Per `session_id` useful, not required for decide correctness. |
| Retries | Audit: retry until committed. Lag is OK. |
| Poison | Malformed audit: DLQ. Do not nack decide (already succeeded). |
| Replay | Required for exam evidence and golden-set incidents. |
| Delivery | At-least-once. Upsert on `decision_id`. |
| Retention | Compliance window. Independent of freeze TTL. |

This plane does **not** consume `{runs_topic}` and does **not** produce job starts.

---

## 8. Sequence diagrams

### Happy path — chat classify → route

![Chat AFD posts decide. The Data Plane intersects the catalogue with claims and channel, returns route, and writes the decision record asynchronously.](./diagrams/plane-seq-decide.svg)

[Editorial diagram](./diagrams/plane-seq-decide.html)

### Happy path — jobs entitle (no Layer ② / ③)

API AFD sends explicit `route_id` + claims. Data Plane looks up, entitles, and records. Entitled → `route`. Missing claims → `abstain` / fail closed. No Layer ② / ③. No `clarify`.

### Failure — Layer ③ saturated

If Layer ③ times out or saturates, return `clarify` or `abstain`. Do not enqueue behind Layer ② and do not slow the hot path.

### Duplicate decide

Two identical chat turns (double-click). Plane may return `route` twice and write two audit rows. AFD/AR idempotency on start prevents two runs. Continuation does not call decide.

---

## 9. Failure and resilience design

| Failure | Behaviour |
| --- | --- |
| Decide replicas down | Classify fails closed. AFD returns 503. No guessed route. |
| Catalogue snapshot missing | Fail closed. Unreadable is not "empty eligible" for operators — it is outage. |
| One AR down | Plane still accepts turns. AFD start-ack fails for that target only. |
| One AFD down | Plane unaffected. Other AFD still decides. |
| Audit lag / audit store down | Decide still succeeds. Exam trail lags. Alert on queue depth, not on decide p99. |
| Layer ③ saturated | `clarify` / `abstain`. Do not enqueue behind Layer ②. |
| Shared down | Unaffected. Routing still works. |
| Stale replica after version bump | New decides must not mix versions in one response. Load the snapshot atomically. In-flight pins keep their version via AFD, not via this replica. |
| Duplicate audit events | Upsert `decision_id`. |
| Regional failure | Fail over decide replicas + catalogue snapshot. Audit can catch up. |

**Retries / backoff:** none on the hot path to AR (this box does not call AR). Layer ② is budgeted, not retried into Layer ③. Audit: exponential backoff + DLQ.

**Circuit breakers:** Layer ③ pool. Catalogue origin (serve last-good snapshot only if it is still the named `active` version; otherwise fail closed — do not serve a previous table as `active`).

**DR:** Catalogue origin is the source for replicas. Audit is replayable from the decision topic. RTO for classify is "restore snapshot + replicas." Do not DR by opening a public Plane URL.

**Anti-patterns:** public Agent Plane URL; pin or start on ACP; re-read `active` after pin; scaling Layer ② by adding Layer ③ replicas; event-only rows on chat chips; entitlements stored per user in the route table; waiting on Temporal / the loop.

---

## Read next

[Agent Front Door](./agent-front-door.md) · [Agent Runtime](./agent-runtime.md) · [Agent Capability Registry](./agent-capability-registry.md) · [Behaviour source](./narrative/agent-plane.mdx)
