# kyc_onboarding

Route id: `kyc_onboarding` · version `2026.08.1` · Pattern 2 (deterministic) with **designer-owned branch**.

Fixed KYC pipeline. After `kyc_risk_engine` returns a `risk` slot, the workflow `branch` map picks the next stage — the model does not choose.

| Stage | Tool | `llm_role` | Notes |
| --- | --- | --- | --- |
| `collect_docs` | `kyc_doc_intake` | `none` | HTTP from `goal.applicant_id` |
| `identity_check` | `kyc_id_verify` | `none` | |
| `sanctions_screen` | `kyc_sanctions_api` | `none` | |
| `risk_score` | `kyc_risk_engine` | `none` | **`branch`**: `high` → `manual_review`, `low` → `activate_account` |
| `manual_review` | — | — | `type=human_gate` — run pauses until `/turns` resume |
| `activate_account` | `kyc_account_activate` | `none` | Side-effect write (`requires_approval`) |
| `summarize` | — | `synthesis` | Ops summary from prior `notes` |

## Branch demo

Mock risk engine (`POST /kyc/risk`):

- `applicant_id` containing `app-high` or `high-risk` → `risk: "high"` → **human gate** (`status=waiting`)
- any other applicant id → `risk: "low"` → **activate** → completed summary

```bash
./agent-fabric-scripts/stack/route/kyc_onboarding/add.sh
```

Job demos: [http://localhost:3014/jobs](http://localhost:3014/jobs)

Low-risk job goal:

```json
{
  "applicant_id": "app-low-4412"
}
```

High-risk job goal (pauses at gate):

```json
{
  "applicant_id": "app-high-9910"
}
```

Resume after manual review: open [Human scratchpad](http://localhost:3014/human), paste the `correlation_id`, and submit the gate packet — or:

```http
POST /v1/jobs/{correlation_id}/turns
{"decision":"approve","reviewer":"ops-jane","notes":"Approved after doc check"}
```

Required claim: `kyc:operate`

Remove: `./remove.sh`
