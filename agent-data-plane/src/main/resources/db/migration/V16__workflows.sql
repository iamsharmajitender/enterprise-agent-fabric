CREATE TABLE dataplane.workflows (
  workflow_id TEXT NOT NULL,
  workflow_version TEXT NOT NULL,
  description TEXT,
  stages JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL,
  PRIMARY KEY (workflow_id, workflow_version),
  CONSTRAINT workflows_status_chk
    CHECK (status IN ('draft', 'published', 'deprecated'))
);

CREATE UNIQUE INDEX workflows_one_published
  ON dataplane.workflows (workflow_id)
  WHERE status = 'published';

INSERT INTO dataplane.workflows (
  workflow_id, workflow_version, description, stages, status
) VALUES
(
  'kyc_onboarding_v2',
  '2026.08.1',
  'Fixed KYC onboarding stages with a risk branch and gated activation',
  $$[
    {"id":"collect_docs","tool":"doc_intake"},
    {"id":"identity_check","tool":"id_verify"},
    {"id":"sanctions_screen","tool":"sanctions_api"},
    {"id":"risk_score","tool":"kyc_risk_engine","branch":{"high":"manual_review","low":"activate_account"}},
    {"id":"manual_review","type":"human_gate"},
    {"id":"activate_account","tool":"account_activate","side_effect":true,"requires_approval":true}
  ]$$::jsonb,
  'published'
),
(
  'msa_risk_review_v1',
  '2026.08.1',
  'Fixed MSA risk review stages: OCR, retrieve, score, memo',
  $$[
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"query_formulation"},
    {"id":"risk_engine","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb,
  'published'
);
