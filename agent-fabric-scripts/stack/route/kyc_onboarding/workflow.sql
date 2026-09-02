-- kyc_onboarding — fixed Pattern 2 stage list with branch + human_gate.

\c adp
INSERT INTO dataplane.workflows (
  workflow_id, workflow_version, description, stages, status
) VALUES
(
  'kyc_onboarding', '2026.08.1',
  'Pattern 2 KYC: doc intake → verify → sanctions → risk (branch) → manual_review gate or activate → synthesis',
  $$[
    {"id":"collect_docs","tool":"kyc_doc_intake","llm_role":"none"},
    {"id":"identity_check","tool":"kyc_id_verify","llm_role":"none"},
    {"id":"sanctions_screen","tool":"kyc_sanctions_api","llm_role":"none"},
    {"id":"risk_score","tool":"kyc_risk_engine","llm_role":"none","branch":{"high":"manual_review","low":"activate_account"}},
    {"id":"manual_review","type":"human_gate"},
    {"id":"activate_account","tool":"kyc_account_activate","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"summarize","llm_role":"synthesis"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (workflow_id, workflow_version) DO UPDATE SET
  description = EXCLUDED.description,
  stages = EXCLUDED.stages,
  status = EXCLUDED.status;
