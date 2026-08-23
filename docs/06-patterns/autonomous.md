# Autonomous (Pattern 1)

The **LLM picks the next step**. The route points at a **tool manifest** and `max_loop_steps`. There is **no workflow**. Runtime runs a `CALL` / `DONE` loop: the model proposes a capability from the hydrated manifest, the app executes it, observes, and loops until `DONE` or the budget is exhausted.

Two runs with the same goal may take different paths. Both can be valid. The app owns the budget; the LLM only proposes.

Tools are required. Pattern 1 with an empty manifest is not a product.

```
goal  →  LLM (CALL or DONE)
              │
              ├─ CALL capability  →  HTTP (domain or agent child)  →  observe  →  LLM again
              └─ DONE  →  answer
```

`max_loop_steps` caps the whole loop (decide → tool → observe), across all tools combined. It is not “each tool may run N times.”

## How it is hooked together

The route row has `autonomy_mode=1`, `prompt_id`, `tool_manifest` + version, and `max_loop_steps`. It has **no** `workflow_id`.

```
Front Door POST /v1/runs
        │
        ▼
   pin  route_id + route_version     goal immutable
        │
        ▼
   hydrate  ACR GET manifest + each capability     invoke.url freezes on the pin
            no workflow → every tool llm_role=none
            _ensure_llm does not append respond — the loop is the LLM
        │
        ▼
   graph    build_agent_loop (agent-runtime/app/core/agent_core.py, mode == 1)
            not START → n0 → n1. LLM port required. No mid-loop ACR GET.
        │
        ▼
   each step
            llm.complete → CALL <id>  →  _run_stage HTTP (llm_role forced none)
                         → DONE <answer>  →  result
            cap = max_loop_steps (decide → tool → observe, all tools combined)
        │
        ▼
   attachments
            prefetch: pack scope before the first decide (not a CALL)
            retrieval.mode=tool: ordinary manifest id the model may CALL or skip
            memory: working notes after each CALL; loop=checkpoint cursor
            kind=agent: CALL starts another catalogue product (new freeze)
```

Data that moves: HTTP payload is `dict(goal)` only. Tool `text` / `message` appends to `notes`. The next decide reads those notes. HTTP never reads `notes`. See [data](../02-understand/data.md).

This Runtime: prefetch is a no-op; `kind=agent` HTTP is skipped; `conversation` / `long_term` are catalogue-only. Gaps: [status](../02-understand/status.md).

## Swimlane

![Pattern 1 swimlane](diagrams/pattern-1-swimlane.svg)

Front Door starts. Runtime pins (no workflow). Catalogue hydrates the manifest. The LLM **CALL**s or **DONE**s; CALL hits domain HTTP and notes loop back. [Open as a page](diagrams/pattern-1-swimlane.html).

## How the LLM is called

Every loop step is one `llm.complete(system, user)` inside `build_agent_loop` (`agent-runtime/app/graph/workflow.py`). Domain HTTP runs **between** those calls, never instead of them.

| Message | Source |
| --- | --- |
| **system** | Fixed contract (`CALL <tool_id>` or `DONE <answer>`), plus pack `host` (same extra text every turn, from `prompt_id`), plus `Tools: id1, id2, …` from the hydrated manifest. |
| **user** | `_user_blob`: `goal: {…}` and `prior stage outputs:` (tool strings accumulated so far). |

The model must reply with **one line**:

- `CALL <tool_id>` — lookup that id on the pin, force `llm_role=none`, POST `dict(goal)` to `invoke.url`, append `text`/`message` to `notes`, loop.
- `DONE <answer>` — that answer is `result`. Loop ends. On_stage records this as `respond`.

Unknown tool id fails the run. Exceeding `max_loop_steps` fails the run. A retrieve capability is just another CALL. Prefetch is not a CALL. Pattern 1 uses `host` only — it does not stamp `by_llm_role` onto tools ([prompts](../02-understand/prompts.md)).

## What you may attach

| Attachment | Allowed | Role |
| --- | --- | --- |
| Manifest | required | Every tool the model may `CALL` |
| Workflow | omit | A stage list would fight the loop |
| Retrieval omit | yes | No corpus. Web search and domain APIs are still tools |
| Retrieval prefetch | yes | App packs `scope` **before** the first decide. Model cannot skip the pack. It still chooses later tools |
| Retrieval tool | yes | Named retrieve capability on the manifest. Model may skip it |
| Memory omit | yes | One-shot job loop. Death loses the scratch pad |
| Memory session | yes | `conversation` + `working`; author `loop=checkpoint` so a crash has a cursor. `long_term=retrieve_only` only when retrieve exists |
| `kind=agent` | yes | A manifest tool that starts another catalogue product (new freeze, new entitle) |

One tool vs many tools is the same pattern. A smaller manifest is not a new mode.

Web search is not corpus RAG. Omit the retrieval row when the tools are the open web (`search_only`, `research_assistant`).

## Supported compositions

Retrieval × memory, tools always on. Child start is an overlay.

| # | Retrieval | Memory | Product | Seed illustration |
| --- | --- | --- | --- | --- |
| 1 | omit | no | One-shot open loop | not in seed |
| 2 | omit | yes | Research / search chat | `search_only`, `research_assistant` |
| 3 | prefetch | no | Pack then explore, one-shot | not in seed |
| 4 | prefetch | yes | Pack then explore, sticky | `fraud_one_tool`, `fraud_casefile` |
| 5 | tool | no | LLM may retrieve, one-shot | not in seed |
| 6 | tool | yes | LLM may retrieve, sticky | `fee_explain`, `contract_investigation` |
| 7 | any | usually yes | Loop may start a child agent | `fraud_investigate`, `ops_start_kyc` |

---

## 1. Open loop, no index, one-shot

Manifest only. No retrieval row. No memory row. The model chooses tools until `DONE`. Use for a fire-and-forget job whose path is unknown and whose notes must not outlive the run.

---

## 2. Open loop, no index, session

Same loop. Session policy keeps conversation, working notes, and a loop checkpoint.

**Use when** the product is exploration over tools that are not a named corpus: web search, fetch URL, draft a brief.

Seed: `search_only` (`web_search`); `research_assistant` (`web_search`, `fetch_url`, `note_store`, `draft_brief`).

---

## 3. Open loop + prefetch, one-shot

Before the first decide, pack `scope`. The model then chooses other tools. It cannot skip the pack. It can skip later tools.

**Use when** grounding must happen, the path after that is unknown, and there is no follow-up turn.

---

## 4. Open loop + prefetch, session

Prefetch plus memory. Packed chunks land in working memory; later `CALL`s and a later turn can see them. Loop checkpoint covers a long tool path.

**Use when** an investigation must be grounded up front (accounts, casefile) and the model still chooses OCR / risk / memo order.

Seed: `fraud_one_tool` (prefetch `accounts`, tool `draft_memo`); `fraud_casefile` (prefetch `accounts`, tools `ocr_extract`, `risk_engine`, `draft_memo`).

---

## 5. Open loop + retrieve-as-tool, one-shot

A retrieve capability sits on the manifest like any other `domain` tool. `retrieval.mode=tool` and `scope` name the corpora that tool may hit. The model may call it, skip it, or call it twice, within `max_loop_steps`.

**Use when** search is optional and the job is one-shot.

---

## 6. Open loop + retrieve-as-tool, session

Same as 5, with conversation, working, loop checkpoint, and usually `long_term=retrieve_only` so later journeys recall facts via retrieve rather than a stuffed prompt.

**Use when** the model should decide whether and when to search, and the thread or investigation continues.

Seed: `fee_explain` (tool `account_fee_lookup`, scope `accounts`); `contract_investigation` (OCR plus clause/policy search, scope `clause-index`, `legal-playbook`).

---

## 7. Child agent overlay

A manifest entry with `kind=agent` starts **another catalogue product**: Front Door `POST /v1/jobs` with a fixed `route_id` in the invoke body. New freeze, new entitle, callee `agent_client_id`. The parent LLM proposes the capability id, not a free route. Parent notes do not automatically merge into the child `goal` unless you define that projection.

This overlay sits on compositions 1–6. Retrieval on the parent is independent of the child route’s own retrieval.

**Use when** the unknown path includes “hand this packet to another product” (Legal review, KYC).

Seed: `fraud_investigate` (`start_contract_review` → `contract_review`); `ops_start_kyc` (`start_kyc_onboarding` → `kyc_onboarding`).

---

## Not autonomous

| Shape | Where it lives |
| --- | --- |
| One LLM call, no tools | [single-inference](single-inference.md) |
| Fixed stage order, even if stages call tools | [deterministic](deterministic.md) |
| Fixed stages, LLM chooses tools **inside** a stage | [guided](guided.md) |
