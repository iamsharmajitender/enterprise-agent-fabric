# Scenario matrix: catalogue seed data sharing

Source of truth: `agent-data-plane/.../V1__dataplane.sql`, `agent-capability-registry/.../V1__registry.sql`, `agent-fabric-scripts/route-runs/job/jobs.json`.

Share kinds: `goal_only` | `notes_to_llm` | `json_to_http` | `prefetch_pack` | `branch` | `human_gate` | `agent` | `none`

| route_id | pattern | workflow / manifest | share kind | stage handoff (json_to_http) | notes |
| --- | --- | --- | --- | --- | --- |
| `fee_explain` | 1 | `fee_explain` manifest | `goal_only` | — | Single tool; ingress utterance in `goal` |
| `llm_pipeline` | 2 | `llm_pipeline` | `notes_to_llm` | — | Three LLM stages; no domain HTTP |
| `policy_memo` | 2 | `policy_memo` | `prefetch_pack` | prefetch → generate (packed chunks) | D6–D7 |
| `account_notify` | 2 | `account_notify` | `goal_only` | — | `account_id` in job payload |
| `card_freeze` | 2 | `card_freeze` | `goal_only` | — | `card_id` / `account_id` in job payload today; identity/limit mocks return prose only |
| `dispute_intake` | 2 | `dispute_intake` | `goal_only` | — | `dispute_id` in payload |
| `purchase_refund` | 2 | `purchase_refund` | `json_to_http` | `extract_fields` → `match_purchase`: **merchant, amount, date** | **D5 proof route**; ingress has `doc_id`, `account_id` only |
| `pack_then_notify` | 2 | `pack_then_notify` | `prefetch_pack` | prefetch → notify | D6–D7 |
| `pack_then_freeze` | 2 | `pack_then_freeze` | `prefetch_pack` + `goal_only` | prefetch then card HTTP chain | D6–D7 |
| `pack_then_review` | 2 | `pack_then_review` | `prefetch_pack` | prefetch → ocr/score/memo | D6–D7 |
| `clause_lookup` | 2 | `clause_lookup` | `notes_to_llm` | query_formulation → HTTP search | LLM writes query string |
| `template_retrieve` | 2 | `template_retrieve` | `notes_to_llm` | two query_formulation stages | |
| `msa_risk_review` | 2 | `msa_risk_review` | `notes_to_llm` + `json_to_http` (future) | ocr JSON → score (optional D5 alt) | query stages use notes; score could consume OCR slot |
| `kyc_onboarding` | 2 | `kyc_onboarding` | `json_to_http` + `branch` + `human_gate` | risk_score slot → branch keys | D8–D9 |
| `claims_adjudicate` | 2 | `claims_adjudicate` | `notes_to_llm` | forced retrieve then clause retrieve | |
| `ticket_triage` | 3 | `ticket_triage` | `goal_only` | — | |
| `product_explain` | 3 | `product_explain` | `prefetch_pack` | | D6–D7 |
| `narrow_review` | 3 | `narrow_review` | `notes_to_llm` | | |
| `contract_review` | 3 | `contract_review` | `notes_to_llm` | | |
| `due_diligence` | 3 | `due_diligence` | `notes_to_llm` | | |
| `fraud_investigate` | 1 + agent | manifest + `start_contract_review` | `agent` | parent → child projection | D10 |
| `ops_start_kyc` | 1 + agent | manifest + `start_kyc_onboarding` | `agent` | parent → child projection | D10 |
| `agent-chat`, `email_summarize`, `chat_session`, `agent-policy-qa`, `policy_chat` | 0 | prompt only | `none` / `prefetch_pack` (policy) | | Pattern 0 |
| `search_only`, `research_assistant`, `contract_investigation` | 1 | manifest | `goal_only` | | Pattern 1 loops |
| `conversation` / `long_term` memory flags | — | — | **out of plan** | — | Shared Memory ([future-enhancement](../tasks/future-enhancement.md)) |

**D5 proof route:** `purchase_refund` — `match_purchase` requires `merchant`, `amount`, and `date` from the `extract_fields` classify slot; they are not in the job payload.
