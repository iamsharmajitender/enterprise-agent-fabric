# Dummy jobs and chats

Local scripts for every **teaching job route** and every **chat-visible route** in [`../seed/create-seed-data.sql`](../seed/create-seed-data.sql).

Jobs `POST /v1/jobs`. They skip keyword classify. Front Door entitles Layer ① (active catalogue ∩ claims), freezes, starts Runtime, and returns `202 { "correlation_id" }`. `fee_explain` is in both catalogues: jobs (`1-autonomous/fee_explain.sh`) and chat (`chat/1-autonomous/fee_explain.sh`).

Chats `POST /v1/assistant/turns`. `fee_explain` uses keyword classify (`Why was I charged $42?`). Routes that share keywords pin a hint chip instead. Chat JSON is FR-5 slim (`route_id` / `run_id` stay off the wire).

## Fresh ids every run

Each invocation mints:

| Field | Who | Shape |
| --- | --- | --- |
| `idempotency_key` | this folder (jobs) | `job-{route_id}:{token}` |
| payload ids (`account_id`, `claim_id`, …) | this folder | `{id}` in [`jobs.json`](jobs.json) / [`chats.json`](chats.json) replaced with the same token |
| `correlation_id` | Front Door / Runtime | `corr-…` (jobs) |
| `session_id` | Front Door | `sess-…` (chats) |

Hitting the same script twice creates **two** jobs or **two** chat sessions.

## Test idempotency

`--check-idempotency` mints **one** key, `POST`s it twice, and fails if the two `correlation_id`s differ. Look for `idempotency_ok=true`.

```bash
./docs/run/dummy-jobs/run-job.sh --check-idempotency fee_explain
./docs/run/dummy-jobs/1-autonomous/fee_explain.sh --check-idempotency
./docs/run/dummy-jobs/2-deterministic/claims_adjudicate.sh --check-idempotency
```

Works on any route in this folder. Runtime returns the original id for a duplicate `idempotency_key`; Front Door does not start a second run.

## Run (repo root, fabric up)

```bash
./docs/run/scripts/start-app.sh

./docs/run/dummy-jobs/run-job.sh --list
./docs/run/dummy-jobs/1-autonomous/fee_explain.sh
./docs/run/dummy-jobs/run-job.sh claims_adjudicate
./docs/run/dummy-jobs/run-chat.sh --list
./docs/run/dummy-jobs/chat/1-autonomous/fee_explain.sh
```

### Run all jobs / chats

`--all` posts every teaching job in [`jobs.json`](jobs.json) (fresh ids each time). `--mode N` is the same for one autonomy band (`0` single inference, `1` autonomous, `2` deterministic, `3` guided).

```bash
./docs/run/dummy-jobs/run-job.sh --all
./docs/run/dummy-jobs/run-job.sh --mode 2
./docs/run/dummy-jobs/run-chat.sh --all
./docs/run/dummy-jobs/run-chat.sh --mode 0
```

By default `--all` and `--mode` **only POST** and do not wait for completion. Poll each until `completed` / `failed`:

```bash
WAIT=1 ./docs/run/dummy-jobs/run-job.sh --all
WAIT=1 ./docs/run/dummy-jobs/run-job.sh --mode 2
WAIT=1 ./docs/run/dummy-jobs/run-chat.sh --all
```

Single-route scripts always poll until `completed` / `failed` (or timeout). Override Front Door with `AFD_URL` (default `http://localhost:3005`).

Stub user `jane`. Required claims come from `jobs.json` / `chats.json` (`accounts:read` for `fee_explain`, `claims:read` for `claims_adjudicate`, …). Missing claims → **403**, Runtime is not started. Chat turns that classify to nothing return `abstain` / `clarify`, not 403.

Routes that only call domain tools can finish against tool-mock. LLM stages still need Ollama.

## Layout

| Path | Autonomy | Routes |
| --- | --- | --- |
| [`0-single-inference/`](0-single-inference/) | 0 Single inference | `email_summarize` |
| [`1-autonomous/`](1-autonomous/) | 1 Autonomous | `fee_explain`, `fraud_one_tool`, `fraud_casefile`, `contract_investigation` |
| [`2-deterministic/`](2-deterministic/) | 2 Deterministic | `llm_pipeline`, `policy_memo`, `account_notify`, `card_freeze`, `dispute_intake`, `pack_then_*`, `clause_lookup`, `template_retrieve`, `msa_risk_review`, `kyc_onboarding`, `claims_adjudicate` |
| [`3-guided/`](3-guided/) | 3 Guided | `ticket_triage`, `narrow_review`, `contract_review`, `due_diligence` |

[`jobs.json`](jobs.json) is the job catalogue (route, claims, payload template). Per-route `.sh` files call [`run-job.sh`](run-job.sh). Add a job by appending `jobs.json` and a wrapper in the matching autonomy folder.

## Chat layout

| Path | Autonomy | Routes |
| --- | --- | --- |
| [`chat/0-single-inference/`](chat/0-single-inference/) | 0 Single inference | `agent-chat`, `chat_session`, `agent-policy-qa`, `policy_chat` |
| [`chat/1-autonomous/`](chat/1-autonomous/) | 1 Autonomous | `search_only`, `research_assistant`, `fee_explain` |
| [`chat/3-guided/`](chat/3-guided/) | 3 Guided | `product_explain` |

No teaching chat-visible route is autonomy 2. [`chats.json`](chats.json) is the catalogue (route, claims, utterance). Per-route `.sh` files call [`run-chat.sh`](run-chat.sh). `fee_explain` also checks Control Plane, FR-5, the canned fee line, and the four databases.

APIs: [agent-front-door/README.md](../../../agent-front-door/README.md). Swimlane: [../diagrams/swimlane-jobs-fee-explain.html](../diagrams/swimlane-jobs-fee-explain.html).
