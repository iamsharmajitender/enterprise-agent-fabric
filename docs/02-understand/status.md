# Status

What the catalogue can name versus what this Runtime does. Present tense on the right column is pin-hydrate-graph behaviour in `agent-runtime`. Catalogue-only means ADP stores it and Control Plane shows it; AR does not execute it.

| Capability | Catalogue | This Runtime |
| --- | --- | --- |
| goal on every HTTP tool | yes | yes |
| notes → LLM stages | yes | yes |
| query_formulation adds query | yes | yes |
| tool JSON → next HTTP (slots / fill-by-name) | implied by input schema | NO |
| deterministic_prefetch pack | mode+scope on route | NO (empty invoke) |
| workflow `branch` | stored | NOT executed |
| `human_gate` | stored | NOT executed |
| kind=agent child projection | capability kind | skipped HTTP (no child jobs POST) |
| conversation=session | flag | NO transcript store |
| long_term=retrieve_only | flag | NO |
| loop=checkpoint resume | writes blob | NO resume-from-step |

## How to read the gaps

- **goal / notes / query_formulation** — implemented in `agent-runtime/app/graph/workflow.py`. `GraphState` is `result`, `goal`, `notes`. HTTP body is `payload = dict(goal)`. `query_formulation` sets `payload["query"]`. LLM stages read prior `notes`. Hydrate stamps `llm_role` / `llm_prompt` in `agent-runtime/app/agents/hydrate.py`.
- **Slots / fill-by-name** — capability input schema does not copy `identity_check` JSON into `freeze_card`. See [data](data.md).
- **deterministic_prefetch** — `policy_memo` does not POST the corpus gateway. Prefetch `invoke` is empty. See [retrieve](retrieve.md).
- **branch / human_gate** — linear LangGraph only (`kyc_onboarding` names both). See [patterns](patterns.md).
- **kind=agent** — child start is AFD `POST /v1/jobs` with a new goal body. Teaching parents: `fraud_investigate` (`start_contract_review` → `contract_review`) and `ops_start_kyc` (`start_kyc_onboarding` → `kyc_onboarding`). Runtime skips that HTTP today. Parent `notes` are not merged. Projection of parent fields into the child goal is not built. See [capabilities](capabilities.md).
- **conversation / long_term** — flags on `dataplane.memory_profiles`. Not a Shared Memory box. See [memory](memory.md).
- **loop=checkpoint** — cursor JSON is written. Continuing the graph from `checkpoint.step` after a crash is not wired.

Later work: [dataflow-plan.md](../tasks/dataflow-plan.md). Do not treat dummy `--all` green as dataflow. Teaching matrix: [03-catalogue](../03-catalogue/). Contracts: [05-reference](../05-reference/). Box packs: [04-architecture](../04-architecture/).
