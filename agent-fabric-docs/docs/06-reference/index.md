---
title: Reference
sidebar_label: Overview
---

# Reference

Frozen request/response examples. They are **not** a live OpenAPI spec and the running services do not serve this folder.

Docs map: [documentation map](/). Stub headers: [stub auth](/reference/stub-auth).

## Auth

| File | What |
| --- | --- |
| [stub auth](/reference/stub-auth) | Channel `Bearer stub` + `X-Stub-Claims`; workload `Bearer fabric-internal` + `X-Workload` |

## Decide (Data Plane)

`POST /v1/intent/decide`

| File | What |
| --- | --- |
| [decide-chat-request.json](/fixtures/decide-chat-request.json) | Chat decide request |
| [decide-chat-route.json](/fixtures/decide-chat-route.json) | Chat decide `outcome=route` (`fee_explain`) |
| [decide-chat-clarify.json](/fixtures/decide-chat-clarify.json) | Chat decide `outcome=clarify` |
| [decide-chat-abstain.json](/fixtures/decide-chat-abstain.json) | Chat decide `outcome=abstain` |
| [decide-jobs-route.json](/fixtures/decide-jobs-route.json) | Jobs decide (`ingress: "jobs"`, `route_id` set) |

## Chat (Front Door)

`POST /v1/assistant/turns`

| File | What |
| --- | --- |
| [assistant-turn-request.json](/fixtures/assistant-turn-request.json) | Chat turn body |
| [assistant-turn-accepted.json](/fixtures/assistant-turn-accepted.json) | Chat turn accepted |

## Jobs (Front Door)

`POST /v1/jobs`

| File | What |
| --- | --- |
| [jobs-start.json](/fixtures/jobs-start.json) | Start `fee_explain` |
| [jobs-start-claims-adjudicate.json](/fixtures/jobs-start-claims-adjudicate.json) | Start `claims_adjudicate` |
| [jobs-accepted.json](/fixtures/jobs-accepted.json) | `202 { "correlation_id" }` |

## Runtime

`POST /v1/runs`

| File | What |
| --- | --- |
| [run-start.json](/fixtures/run-start.json) | AR start after pin |
| [run-status-completed.json](/fixtures/run-status-completed.json) | Run status `completed` |

## Capabilities and manifests (Registry)

| File | What |
| --- | --- |
| [capability-account-fee-lookup.json](/fixtures/capability-account-fee-lookup.json) | Domain capability `account_fee_lookup` |
| [capability-ocr-extract.json](/fixtures/capability-ocr-extract.json) | Domain capability `ocr_extract` |
| [capability-extract-fields.json](/fixtures/capability-extract-fields.json) | Domain capability `extract_fields` (classify `output_schema`) |
| [capability-start-contract-review.json](/fixtures/capability-start-contract-review.json) | Agent-start capability `start_contract_review` → `contract_review` |
| [capability-start-kyc-onboarding.json](/fixtures/capability-start-kyc-onboarding.json) | Agent-start capability `start_kyc_onboarding` → `kyc_onboarding` |
| [manifest-fee-explain.json](/fixtures/manifest-fee-explain.json) | Manifest for `fee_explain` |
| [manifest-fraud-investigate.json](/fixtures/manifest-fraud-investigate.json) | Parent manifest `fraud_investigate` (Legal start) |
| [manifest-ops-start-kyc.json](/fixtures/manifest-ops-start-kyc.json) | Parent manifest `ops_start_kyc` (KYC start) |

## Prompts and corpora (Data Plane)

| File | What |
| --- | --- |
| [prompt-email-summarize.json](/fixtures/prompt-email-summarize.json) | Prompt-only pack |
| [prompt-msa-risk-review.json](/fixtures/prompt-msa-risk-review.json) | MSA review pack (`by_llm_role`) |
| [corpus-policy-engine.json](/fixtures/corpus-policy-engine.json) | Published corpus row |
