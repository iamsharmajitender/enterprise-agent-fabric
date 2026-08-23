# Dummy requests

Local scripts for every **seed job route** and every **chat-visible route** in [`../scripts/create-seed-data.sql`](../scripts/create-seed-data.sql).

Jobs `POST /v1/jobs`. They skip keyword classify. Front Door entitles Layer ① (active catalogue ∩ claims), freezes, starts Runtime, and returns `202 { "correlation_id" }`.

Chats `POST /v1/assistant/turns`. Keyword classify unless a hint chip is required. Chat JSON is FR-5 slim (`route_id` / `run_id` stay off the wire).

`fee_explain` is both: [`job/1-autonomous/fee_explain.sh`](job/1-autonomous/fee_explain.sh) and [`chat/1-autonomous/fee_explain.sh`](chat/1-autonomous/fee_explain.sh).

## Layout

Both channels use the same tree: catalogue JSON + wrappers grouped by autonomy.

| Path | Channel | Catalogue |
| --- | --- | --- |
| [`job/`](job/) | `POST /v1/jobs` | [`job/jobs.json`](job/jobs.json) |
| [`chat/`](chat/) | `POST /v1/assistant/turns` | [`chat/chats.json`](chat/chats.json) |

| Folder | Autonomy | Jobs | Chat |
| --- | --- | --- | --- |
| `0-single-inference/` | 0 | `email_summarize` | `agent-chat`, `chat_session`, `agent-policy-qa`, `policy_chat` |
| `1-autonomous/` | 1 | `fee_explain`, `fraud_one_tool`, `fraud_casefile`, `fraud_investigate`, `ops_start_kyc`, `contract_investigation` | `search_only`, `research_assistant`, `fee_explain` |
| `2-deterministic/` | 2 | `llm_pipeline`, `policy_memo`, `account_notify`, `card_freeze`, `dispute_intake`, `pack_then_*`, `clause_lookup`, `template_retrieve`, `msa_risk_review`, `kyc_onboarding`, `claims_adjudicate` | — (no seed chat-visible route) |
| `3-guided/` | 3 | `ticket_triage`, `narrow_review`, `contract_review`, `due_diligence` | `product_explain` |

Add a request by appending the channel JSON and a wrapper in the matching autonomy folder. Wrappers call [`run-job.sh`](run-job.sh) or [`run-chat.sh`](run-chat.sh).

## Fresh ids every run

Each invocation mints:

| Field | Who | Shape |
| --- | --- | --- |
| `idempotency_key` | this folder (jobs) | `job-{route_id}:{token}` |
| payload ids (`account_id`, `claim_id`, …) | this folder | `{id}` in the channel JSON replaced with the same token |
| `correlation_id` | Front Door / Runtime | `corr-…` (jobs) |
| `session_id` | Front Door | `sess-…` (chats) |

Hitting the same script twice creates **two** jobs or **two** chat sessions.

## Test idempotency (jobs)

`--check-idempotency` mints **one** key, `POST`s it twice, and fails if the two `correlation_id`s differ. Look for `idempotency_ok=true`.

```bash
./docs/run/dummy-request/run-job.sh --check-idempotency fee_explain
./docs/run/dummy-request/job/1-autonomous/fee_explain.sh --check-idempotency
./docs/run/dummy-request/job/2-deterministic/claims_adjudicate.sh --check-idempotency
```

Runtime returns the original id for a duplicate `idempotency_key`; Front Door does not start a second run.

## Run (repo root, fabric up)

```bash
./docs/run/scripts/start-app.sh

./docs/run/dummy-request/run-job.sh --list
./docs/run/dummy-request/job/1-autonomous/fee_explain.sh
./docs/run/dummy-request/run-job.sh claims_adjudicate
./docs/run/dummy-request/run-chat.sh --list
./docs/run/dummy-request/chat/1-autonomous/fee_explain.sh
```

### Run all jobs / chats

`--all` posts every row in the channel JSON (fresh ids each time). `--mode N` is the same for one autonomy band (`0` single inference, `1` autonomous, `2` deterministic, `3` guided).

```bash
./docs/run/dummy-request/run-job.sh --all
./docs/run/dummy-request/run-job.sh --mode 2
./docs/run/dummy-request/run-chat.sh --all
./docs/run/dummy-request/run-chat.sh --mode 0
```

By default `--all` and `--mode` **only POST** and do not wait for completion. Poll each until `completed`. `WAIT=1` is fail-closed (non-zero on `failed` or timeout):

```bash
WAIT=1 ./docs/run/dummy-request/run-job.sh --all
WAIT=1 ./docs/run/dummy-request/run-job.sh --mode 2
WAIT=1 ./docs/run/dummy-request/run-chat.sh --all
WAIT=1 ./docs/run/dummy-request/run-chat.sh --mode 0
```

Single-route scripts always poll until `completed` / `failed` (or timeout). Override Front Door with `AFD_URL` (default `http://localhost:3005`).

Stub user `jane`. Required claims come from the channel JSON (`accounts:read` for `fee_explain`, `claims:read` for `claims_adjudicate`, …). Missing claims → **403**, Runtime is not started. Chat turns that classify to nothing return `abstain` / `clarify`, not 403.

Routes that only call domain tools can finish against tool-mock. LLM stages still need Ollama.

The `fee_explain` chat wrapper also checks Control Plane, FR-5, the canned fee line, and the four databases.

APIs: [agent-front-door/README.md](../../../agent-front-door/README.md). Docs map: [docs/README.md](../../README.md).
