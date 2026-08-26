-- Baseline schema + catalogue seed for database adp.
CREATE SCHEMA IF NOT EXISTS dataplane;

CREATE TABLE dataplane.model_profiles (
  id TEXT PRIMARY KEY,
  typical_use TEXT NOT NULL
);

CREATE TABLE dataplane.corpora (
  corpus_id     TEXT PRIMARY KEY,
  display_name  TEXT NOT NULL,
  url           TEXT NOT NULL,
  collection    TEXT,
  auth          TEXT NOT NULL DEFAULT 'workload-oauth',
  owner         TEXT NOT NULL,
  status        TEXT NOT NULL CHECK (status IN ('draft', 'published', 'deprecated')),
  region        TEXT,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dataplane.manifests (
  manifest_id TEXT NOT NULL,
  manifest_version TEXT NOT NULL,
  description TEXT,
  tools JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'published',
  PRIMARY KEY (manifest_id, manifest_version),
  CONSTRAINT manifests_status_chk CHECK (status IN ('draft', 'published', 'retired'))
);

CREATE TABLE dataplane.prompt_packs (
  prompt_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  host TEXT NOT NULL,
  status TEXT NOT NULL,
  owner TEXT NOT NULL,
  PRIMARY KEY (prompt_id, prompt_version),
  CONSTRAINT prompt_packs_status_chk CHECK (status IN ('draft', 'published', 'deprecated'))
);

CREATE TABLE dataplane.prompt_role_templates (
  prompt_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  llm_role TEXT NOT NULL,
  task_type TEXT NOT NULL,
  text TEXT NOT NULL,
  PRIMARY KEY (prompt_id, prompt_version, llm_role),
  FOREIGN KEY (prompt_id, prompt_version)
    REFERENCES dataplane.prompt_packs (prompt_id, prompt_version),
  CONSTRAINT prompt_role_templates_llm_role_chk CHECK (llm_role <> 'none'),
  CONSTRAINT prompt_role_templates_task_type_chk
    CHECK (task_type IN ('plan', 'synthesize', 'classify'))
);

CREATE TABLE dataplane.workflows (
  workflow_id TEXT NOT NULL,
  workflow_version TEXT NOT NULL,
  description TEXT,
  stages JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL,
  PRIMARY KEY (workflow_id, workflow_version),
  CONSTRAINT workflows_status_chk CHECK (status IN ('draft', 'published', 'deprecated'))
);

CREATE UNIQUE INDEX workflows_one_published
  ON dataplane.workflows (workflow_id)
  WHERE status = 'published';

CREATE TABLE dataplane.routes (
  route_id TEXT NOT NULL,
  intent_label TEXT NOT NULL,
  description TEXT,
  activation_target TEXT,
  agent_client_id TEXT,
  tool_manifest TEXT,
  tool_manifest_version TEXT,
  policy_profile TEXT NOT NULL,
  model_profile TEXT NOT NULL,
  workflow_id TEXT,
  prompt_id TEXT,
  output_schema_id TEXT,
  eval_suite_id TEXT,
  max_loop_steps INTEGER,
  fallback TEXT,
  required_claims JSONB NOT NULL DEFAULT '[]'::jsonb,
  channels JSONB NOT NULL DEFAULT '["web"]'::jsonb,
  chat_visible BOOLEAN NOT NULL DEFAULT TRUE,
  keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
  route_version TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  status TEXT NOT NULL DEFAULT 'published',
  autonomy_mode SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY (route_id, route_version),
  CONSTRAINT routes_autonomy_mode_chk CHECK (autonomy_mode >= 0 AND autonomy_mode <= 3),
  CONSTRAINT routes_status_chk CHECK (status IN ('draft', 'published', 'active', 'retired')),
  CONSTRAINT routes_status_active_chk CHECK (
    (active AND status = 'active') OR ((NOT active) AND status <> 'active')
  ),
  CONSTRAINT routes_model_profile_fk FOREIGN KEY (model_profile)
    REFERENCES dataplane.model_profiles (id),
  CONSTRAINT routes_tool_manifest_fk FOREIGN KEY (tool_manifest, tool_manifest_version)
    REFERENCES dataplane.manifests (manifest_id, manifest_version)
);

CREATE UNIQUE INDEX dataplane_one_active_version_per_route
  ON dataplane.routes (route_id)
  WHERE active;

CREATE TABLE dataplane.retrieval (
  route_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  scope JSONB NOT NULL DEFAULT '[]'::jsonb,
  route_version TEXT NOT NULL,
  PRIMARY KEY (route_id, route_version),
  CONSTRAINT retrieval_route_fk FOREIGN KEY (route_id, route_version)
    REFERENCES dataplane.routes (route_id, route_version)
);

CREATE TABLE dataplane.memory_profiles (
  route_id TEXT NOT NULL,
  conversation TEXT,
  working TEXT,
  "loop" TEXT,
  long_term TEXT,
  ttl_hours INTEGER,
  isolation JSONB NOT NULL DEFAULT '[]'::jsonb,
  route_version TEXT NOT NULL,
  PRIMARY KEY (route_id, route_version),
  CONSTRAINT memory_profiles_route_fk FOREIGN KEY (route_id, route_version)
    REFERENCES dataplane.routes (route_id, route_version)
);

INSERT INTO dataplane.model_profiles (id, typical_use) VALUES
  (
    'reasoning-standard',
    'Plan / multi-step / high-stakes synthesis. Capability matrix + most route examples.'
  ),
  (
    'fast-chat',
    'Cheap synthesize / classify. Capability matrix + inference handoff.'
  ),
  (
    'lightweight-chat',
    'No-tools / cheap chat. Route contract examples (general_chat, escalate_human). Same idea as fast-chat.'
  );

INSERT INTO dataplane.corpora (
  corpus_id, display_name, url, collection, auth, owner, status, region
) VALUES
(
  'policy-engine',
  'Policy engine',
  'http://agent-mocks:3010/v1/search/assistant',
  'policy-engine',
  'workload-oauth',
  'policy-ops',
  'published',
  NULL
),
(
  'clause-index',
  'Clause index',
  'http://agent-mocks:3010/v1/search/legal',
  'clause-index',
  'workload-oauth',
  'legal',
  'published',
  NULL
),
(
  'legal-playbook',
  'Legal playbook',
  'http://agent-mocks:3010/v1/search/legal',
  'legal-playbook',
  'workload-oauth',
  'legal',
  'published',
  NULL
),
(
  'product-faq',
  'Product FAQ',
  'http://agent-mocks:3010/v1/search/assistant',
  'product-faq',
  'workload-oauth',
  'assistant-platform',
  'published',
  NULL
),
(
  'accounts',
  'Accounts',
  'http://agent-mocks:3010/v1/search/assistant',
  'accounts',
  'workload-oauth',
  'assistant-platform',
  'published',
  NULL
),
(
  'sanctions-lists',
  'Sanctions lists',
  'http://agent-mocks:3010/v1/search/kyc',
  'sanctions-lists',
  'workload-oauth',
  'kyc-ops',
  'published',
  NULL
),
(
  'kyc-policy',
  'KYC policy',
  'http://agent-mocks:3010/v1/search/kyc',
  'kyc-policy',
  'workload-oauth',
  'kyc-ops',
  'published',
  NULL
),
(
  'research-index',
  'Research index',
  'http://agent-mocks:3010/corpora/research-index/search',
  'research-index',
  'workload-oauth',
  'assistant-platform',
  'draft',
  NULL
);
-- Catalogue seed with unversioned ids.

-- Pattern 0–3 catalogue seed. Safe to re-run after delete-seed-data.sql.

INSERT INTO dataplane.corpora (
  corpus_id, display_name, url, collection, auth, owner, status, region
) VALUES
  ('product-terms', 'Product terms', 'http://agent-mocks:3010/corpora/product-terms/search', 'product-terms', 'workload-oauth', 'product', 'published', NULL),
  ('fee-schedule', 'Fee schedule', 'http://agent-mocks:3010/corpora/fee-schedule/search', 'fee-schedule', 'workload-oauth', 'product', 'published', NULL)
ON CONFLICT (corpus_id) DO NOTHING;

INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'search_only', '2026.08.1', 'One web search tool',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'research_assistant', '2026.08.1', 'Open research tools (no corpus retrieve)',
  $$[
    {"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"},
    {"name":"fetch_url","capability_id":"fetch_url","capability_version":"1.0.0","pdp_action":"fetch_url","risk_tier":"low"},
    {"name":"note_store","capability_id":"note_store","capability_version":"1.0.0","pdp_action":"note_store","risk_tier":"low"},
    {"name":"draft_brief","capability_id":"draft_brief","capability_version":"1.0.0","pdp_action":"draft_brief","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'fraud_one_tool', '2026.08.1', 'Draft memo after prefetch',
  '[{"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}]'::jsonb,
  'published'
),
(
  'fraud_casefile', '2026.08.1', 'Non-retrieve fraud tools after prefetch',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'fee_explain', '2026.08.1', 'One retrieve tool for account fees',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'contract_investigate', '2026.08.1', 'Multiple tools including two retrieve tools',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'account_notify', '2026.08.1', 'One notify tool',
  '[{"name":"notify_customer","capability_id":"notify_customer","capability_version":"1.0.0","pdp_action":"notify_customer","risk_tier":"medium"}]'::jsonb,
  'published'
),
(
  'card_freeze', '2026.08.1', 'Multi-tool card freeze write path',
  $$[
    {"name":"identity_check","capability_id":"identity_check","capability_version":"1.0.0","pdp_action":"identity_check","risk_tier":"medium"},
    {"name":"limit_check","capability_id":"limit_check","capability_version":"1.0.0","pdp_action":"limit_check","risk_tier":"medium"},
    {"name":"freeze_card","capability_id":"freeze_card","capability_version":"1.0.0","pdp_action":"freeze_card","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'dispute_intake', '2026.08.1', 'Multi-tool dispute intake',
  $$[
    {"name":"doc_intake","capability_id":"doc_intake","capability_version":"1.0.0","pdp_action":"doc_intake","risk_tier":"low"},
    {"name":"case_open","capability_id":"case_open","capability_version":"1.0.0","pdp_action":"case_open","risk_tier":"medium"},
    {"name":"packet_summarize","capability_id":"packet_summarize","capability_version":"1.0.0","pdp_action":"packet_summarize","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'purchase_refund', '2026.08.1', 'Receipt refund: OCR, classify JSON, match, eligibility, gated refund, synthesis confirm.',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"extract_fields","capability_id":"extract_fields","capability_version":"1.0.0","pdp_action":"extract_fields","risk_tier":"low"},
    {"name":"match_purchase","capability_id":"match_purchase","capability_version":"1.0.0","pdp_action":"match_purchase","risk_tier":"medium"},
    {"name":"refund_eligibility","capability_id":"refund_eligibility","capability_version":"1.0.0","pdp_action":"refund_eligibility","risk_tier":"medium"},
    {"name":"post_refund","capability_id":"post_refund","capability_version":"1.0.0","pdp_action":"post_refund","risk_tier":"high"},
    {"name":"refund_confirm","capability_id":"refund_confirm","capability_version":"1.0.0","pdp_action":"refund_confirm","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'clause_lookup', '2026.08.1', 'One named retrieve tool',
  '[{"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'template_retrieve', '2026.08.1', 'Two retrieve tools plus score',
  $$[
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'msa_risk_review', '2026.08.1', 'Fixed MSA risk review tools',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'kyc_onboarding', '2026.08.1', 'KYC onboarding tools with gated activation',
  $$[
    {"name":"doc_intake","capability_id":"doc_intake","capability_version":"1.0.0","pdp_action":"doc_intake","risk_tier":"low"},
    {"name":"id_verify","capability_id":"id_verify","capability_version":"1.0.0","pdp_action":"id_verify","risk_tier":"medium"},
    {"name":"sanctions_api","capability_id":"sanctions_api","capability_version":"1.0.0","pdp_action":"sanctions_screen","risk_tier":"high"},
    {"name":"kyc_risk_engine","capability_id":"kyc_risk_engine","capability_version":"1.0.0","pdp_action":"kyc_risk_score","risk_tier":"medium"},
    {"name":"account_activate","capability_id":"account_activate","capability_version":"1.0.0","pdp_action":"account_activate","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'claims_adjudicate', '2026.08.1', 'Forced playbook retrieve then named clause retrieve',
  $$[
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'ticket_triage', '2026.08.1', 'Parser and scorer tools, no corpus retrieve',
  $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"tag_intent","capability_id":"tag_intent","capability_version":"1.0.0","pdp_action":"tag_intent","risk_tier":"low"},
    {"name":"draft_reply","capability_id":"draft_reply","capability_version":"1.0.0","pdp_action":"draft_reply","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'product_explain', '2026.08.1', 'Non-retrieve analyse tools after prefetch',
  $$[
    {"name":"score_offer","capability_id":"score_offer","capability_version":"1.0.0","pdp_action":"score_offer","risk_tier":"low"},
    {"name":"compare_options","capability_id":"compare_options","capability_version":"1.0.0","pdp_action":"compare_options","risk_tier":"low"}
  ]$$::jsonb,
  'published'
),
(
  'narrow_review', '2026.08.1', 'Many tools, one retrieve tool in Analyse',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'contract_review', '2026.08.1', 'Guided contract review with multiple retrieve tools',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'due_diligence', '2026.08.1', 'Forced playbook retrieve then allowlisted retrieve',
  $$[
    {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
    {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
),
(
  'pack_then_review', '2026.08.1', 'Tools after playbook prefetch',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
);

INSERT INTO dataplane.workflows (workflow_id, workflow_version, description, stages, status) VALUES
(
  'llm_pipeline', '2026.08.1', 'Pattern 2: three LLM stages (classify then two synthesis). No domain HTTP.',
  $$[
    {"id":"extract","llm_role":"classify"},
    {"id":"rewrite","llm_role":"synthesis"},
    {"id":"format","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'policy_memo', '2026.08.1', 'Pattern 2: prefetch placeholder then one synthesis call. No domain HTTP.',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"generate","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'account_notify', '2026.08.1', 'Pattern 2: one domain HTTP notify, then synthesis confirm.',
  $$[
    {"id":"notify","tool":"notify_customer","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'card_freeze', '2026.08.1', 'Pattern 2: three domain HTTP writes, then synthesis confirm.',
  $$[
    {"id":"identity","tool":"identity_check","llm_role":"none"},
    {"id":"limits","tool":"limit_check","llm_role":"none"},
    {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'dispute_intake', '2026.08.1', 'Pattern 2: two domain HTTP steps, then synthesis on the packet.',
  $$[
    {"id":"intake","tool":"doc_intake","llm_role":"none"},
    {"id":"open","tool":"case_open","llm_role":"none"},
    {"id":"summarize","tool":"packet_summarize","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'purchase_refund', '2026.08.1', 'Pattern 2: OCR, classify receipt JSON, match, eligibility, gated refund. human_gate is catalogue-only.',
  $$[
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"extract_fields","tool":"extract_fields","llm_role":"classify"},
    {"id":"match_purchase","tool":"match_purchase","llm_role":"none"},
    {"id":"eligibility","tool":"refund_eligibility","llm_role":"none"},
    {"id":"manual_review","type":"human_gate"},
    {"id":"post_refund","tool":"post_refund","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"respond","tool":"refund_confirm","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'pack_then_notify', '2026.08.1', 'Pattern 2: prefetch placeholder, domain notify, then synthesis confirm.',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"notify","tool":"notify_customer","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'pack_then_freeze', '2026.08.1', 'Pattern 2: prefetch placeholder, three domain HTTP writes, then synthesis confirm.',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"identity","tool":"identity_check","llm_role":"none"},
    {"id":"limits","tool":"limit_check","llm_role":"none"},
    {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'pack_then_review', '2026.08.1', 'Pattern 2: prefetch placeholder, two domain HTTP tools, then synthesis memo.',
  $$[
    {"id":"prefetch","llm_role":"none"},
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"score","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'clause_lookup', '2026.08.1', 'Pattern 2: LLM writes the retrieve query, HTTP search, then synthesis.',
  $$[
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'template_retrieve', '2026.08.1', 'Pattern 2: two query_formulation retrieves, HTTP score, then synthesis.',
  $$[
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"query_formulation"},
    {"id":"score","tool":"risk_engine","llm_role":"none"},
    {"id":"respond","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'msa_risk_review', '2026.08.1', 'Pattern 2: HTTP OCR, two query_formulation retrieves, HTTP score, synthesis memo.',
  $$[
    {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"query_formulation"},
    {"id":"risk_engine","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'kyc_onboarding', '2026.08.1', 'Pattern 2: domain HTTP KYC tools then synthesis packet. branch and human_gate are catalogue-only.',
  $$[
    {"id":"collect_docs","tool":"doc_intake","llm_role":"none"},
    {"id":"identity_check","tool":"id_verify","llm_role":"none"},
    {"id":"sanctions_screen","tool":"sanctions_api","llm_role":"none"},
    {"id":"risk_score","tool":"kyc_risk_engine","llm_role":"none","branch":{"high":"manual_review","low":"activate_account"}},
    {"id":"manual_review","type":"human_gate"},
    {"id":"activate_account","tool":"account_activate","llm_role":"none","side_effect":true,"requires_approval":true},
    {"id":"summarize","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'claims_adjudicate', '2026.08.1', 'Forced playbook retrieve then named clause retrieve',
  $$[
    {"id":"pack_playbook","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
    {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
    {"id":"score","tool":"risk_engine","llm_role":"none"},
    {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'ticket_triage', '2026.08.1', 'Pattern 3: HTTP parse/tag, then synthesis reply. Stage allowlists are catalogue-only.',
  $$[
    {"id":"extract","tool":"parse_ticket","llm_role":"none","allowlist":["parse_ticket"],"max_tool_calls":2},
    {"id":"analyse","tool":"tag_intent","llm_role":"none","allowlist":["parse_ticket","tag_intent"],"max_tool_calls":4},
    {"id":"reply","tool":"draft_reply","llm_role":"synthesis","allowlist":["draft_reply"],"max_tool_calls":2}
  ]$$::jsonb, 'published'
),
(
  'product_explain', '2026.08.1', 'Pattern 3: prefetch placeholder, HTTP score/compare, then synthesis. Allowlists are catalogue-only.',
  $$[
    {"id":"extract","tool":"score_offer","llm_role":"none","allowlist":["score_offer"],"max_tool_calls":2},
    {"id":"analyse","tool":"compare_options","llm_role":"none","allowlist":["score_offer","compare_options"],"max_tool_calls":4},
    {"id":"explain","llm_role":"synthesis","allowlist":["compare_options"],"max_tool_calls":2}
  ]$$::jsonb, 'published'
),
(
  'narrow_review', '2026.08.1', 'Analyse allowlists one retrieve tool',
  $$[
    {"id":"extract","tool":"ocr_extract","llm_role":"none"},
    {"id":"analyse","allowlist":["clause_search","risk_engine"],"max_tool_calls":4},
    {"id":"report","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'contract_review', '2026.08.1', 'Analyse allowlists multiple retrieve tools',
  $$[
    {"id":"extract","tool":"ocr_extract","llm_role":"none"},
    {"id":"analyse","allowlist":["clause_search","policy_search","risk_engine"],"max_tool_calls":6},
    {"id":"report","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
),
(
  'due_diligence', '2026.08.1', 'Forced playbook retrieve then allowlisted retrieve',
  $$[
    {"id":"extract","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
    {"id":"analyse","allowlist":["clause_search","policy_search","risk_engine"],"max_tool_calls":8},
    {"id":"report","tool":"draft_memo","llm_role":"synthesis"}
  ]$$::jsonb, 'published'
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
  ('agent-chat', '2026.08.1', 'Pattern 0. One synthesis turn. Be a concise corporate assistant. No tools.', 'published', 'assistant-platform'),
  ('email_summarize', '2026.08.1', 'Pattern 0. One synthesis turn. Summarize this email for the banker. No tools. Return short bullets.', 'published', 'assistant-platform'),
  ('chat_session', '2026.08.1', 'Pattern 0. One synthesis turn per message. Continue the conversation. No tools. Do not invent facts.', 'published', 'assistant-platform'),
  ('agent-policy-qa', '2026.08.1', 'Pattern 0. One synthesis turn. Answer from retrieved policy text only. Do not invent policy. Cite chunk ids.', 'published', 'assistant-platform'),
  ('policy_chat', '2026.08.1', 'Pattern 0. One synthesis turn. Answer from prefetched policy chunks. Use session memory. No tools.', 'published', 'assistant-platform'),
  ('search_only', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use web_search before DONE when search can answer. Do not invent results.', 'published', 'assistant-platform'),
  ('research_assistant', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use allowed tools. Prefer primary sources. Do not invent tool results.', 'published', 'assistant-platform'),
  ('fraud_one_tool', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. The case file is already in context. CALL draft_memo before DONE.', 'published', 'fraud-ops'),
  ('fraud_casefile', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use OCR, risk, and draft tools. Do not invent tool results.', 'published', 'fraud-ops'),
  ('fee_explain', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. CALL account_fee_lookup before DONE. Do not invent charges. After a tool result, DONE with that output unless another tool is needed.', 'published', 'assistant-platform'),
  ('contract_investigate', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use only allowed tools. Prefer evidence. Do not invent tool results.', 'published', 'legal-agents'),
  ('fraud_investigate', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use OCR and memo tools. You may CALL start_contract_review. Do not invent tools.', 'published', 'fraud-ops'),
  ('ops_start_kyc', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Parse the ticket. You may CALL start_kyc_onboarding. Do not invent tools.', 'published', 'ops'),
  ('llm_pipeline', '2026.08.1', 'Pattern 2. Do only the current stage. Do not choose the next stage. No tools.', 'published', 'assistant-platform'),
  ('policy_memo', '2026.08.1', 'Pattern 2. Do only the current stage. Draft from prefetched policy only.', 'published', 'assistant-platform'),
  ('account_notify', '2026.08.1', 'Pattern 2. Confirm the notify from stage outputs only. Do not invent send status.', 'published', 'ops'),
  ('card_freeze', '2026.08.1', 'Pattern 2. Confirm the freeze from identity, limit, and freeze outputs only. Do not invent card state.', 'published', 'ops'),
  ('dispute_intake', '2026.08.1', 'Pattern 2. Do only the current stage. Do not open extra cases.', 'published', 'ops'),
  ('purchase_refund', '2026.08.1', 'Pattern 2. Do only the current stage. Do not invent a refund. Classify returns JSON only.', 'published', 'ops'),
  ('pack_then_notify', '2026.08.1', 'Pattern 2. Confirm the notify from stage outputs only. Prefetch chunks may be empty.', 'published', 'ops'),
  ('pack_then_freeze', '2026.08.1', 'Pattern 2. Confirm the freeze from stage outputs only. Prefetch chunks may be empty.', 'published', 'ops'),
  ('pack_then_review', '2026.08.1', 'Pattern 2. Do only the current stage. Draft the memo from packed playbook and stage outputs.', 'published', 'legal-agents'),
  ('clause_lookup', '2026.08.1', 'Pattern 2. Do only the current stage. Do not invent clauses.', 'published', 'legal-agents'),
  ('template_retrieve', '2026.08.1', 'Pattern 2. Do only the current stage. Write the query for this stage corpus only, or synthesize from notes.', 'published', 'legal-agents'),
  ('msa_risk_review', '2026.08.1', 'Pattern 2. You are counsel''s MSA risk-review worker. Do only the current stage. Do not invent tools.', 'published', 'legal-agents'),
  ('kyc_onboarding', '2026.08.1', 'Pattern 2. Summarize KYC evidence for a human reviewer. Do not recommend activation.', 'published', 'kyc-ops'),
  ('claims_adjudicate', '2026.08.1', 'Pattern 2. Do only the current stage. Do not reorder stages.', 'published', 'claims-ops'),
  ('ticket_triage', '2026.08.1', 'Pattern 3. Do only the current stage. Draft the reply from parse and tag outputs. Do not invent stages.', 'published', 'ops'),
  ('product_explain', '2026.08.1', 'Pattern 3. Product terms may already be packed. Explain from score and compare outputs only.', 'published', 'product'),
  ('narrow_review', '2026.08.1', 'Pattern 3. Do only the current stage. Analyse may use clause_search and risk_engine only.', 'published', 'legal-agents'),
  ('contract_review', '2026.08.1', 'Pattern 3. Stay inside the current stage. Analyse may choose among the stage allowlist. Do not invent stages.', 'published', 'legal-agents'),
  ('due_diligence', '2026.08.1', 'Pattern 3. Extract always retrieves the playbook. Analyse may retrieve again. Do not invent stages.', 'published', 'legal-agents');

INSERT INTO dataplane.prompt_role_templates (prompt_id, prompt_version, llm_role, task_type, "text") VALUES
  ('llm_pipeline', '2026.08.1', 'classify', 'classify', 'Extract the requested fields from the input only.'),
  ('llm_pipeline', '2026.08.1', 'synthesis', 'synthesize', 'Rewrite or format using the previous stage output only.'),
  ('policy_memo', '2026.08.1', 'synthesis', 'synthesize', 'Draft the memo from prefetched chunks only. Cite chunk ids.'),
  ('account_notify', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from the notify tool output only.'),
  ('card_freeze', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from identity, limit, and freeze outputs only.'),
  ('dispute_intake', '2026.08.1', 'synthesis', 'synthesize', 'Summarize the dispute packet for a human reviewer. Do not recommend a payout.'),
  ('purchase_refund', '2026.08.1', 'classify', 'classify', 'Extract receipt fields from OCR notes and the goal only. Always emit every output_schema key. Use null when a value is not in the notes; do not invent.'),
  ('purchase_refund', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing refund confirm from match, eligibility, and refund outputs only. Do not invent a payout.'),
  ('pack_then_notify', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from the notify tool output only.'),
  ('pack_then_freeze', '2026.08.1', 'synthesis', 'synthesize', 'Write the user-facing confirm from freeze-path stage outputs only.'),
  ('pack_then_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the memo from packed playbook and stage outputs only.'),
  ('clause_lookup', '2026.08.1', 'query_formulation', 'plan', 'Write the clause-index query from the goal only.'),
  ('clause_lookup', '2026.08.1', 'synthesis', 'synthesize', 'Explain the retrieved clause in plain language. Do not invent text that is not in notes.'),
  ('template_retrieve', '2026.08.1', 'query_formulation', 'plan', 'Write the search query for this stage''s corpus only. Do not pick a different index.'),
  ('template_retrieve', '2026.08.1', 'synthesis', 'synthesize', 'Summarize retrieved clauses, playbook hits, and the score. Do not invent sources.'),
  ('msa_risk_review', '2026.08.1', 'query_formulation', 'plan', 'Write the search query for this stage''s corpus only. Do not pick a different index.'),
  ('msa_risk_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.'),
  ('kyc_onboarding', '2026.08.1', 'synthesis', 'synthesize', 'Summarize KYC stage outputs for a human reviewer. Do not recommend activation.'),
  ('claims_adjudicate', '2026.08.1', 'query_formulation', 'plan', 'Write the clause-index query. Do not skip the forced playbook retrieve.'),
  ('claims_adjudicate', '2026.08.1', 'synthesis', 'synthesize', 'Draft the claims memo from stage outputs only.'),
  ('ticket_triage', '2026.08.1', 'synthesis', 'synthesize', 'Draft the customer reply from parse and tag outputs only.'),
  ('product_explain', '2026.08.1', 'synthesis', 'synthesize', 'Explain the offer from score and compare outputs only. Do not invent rates.'),
  ('narrow_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the memo from Analyse outputs only.'),
  ('contract_review', '2026.08.1', 'synthesis', 'synthesize', 'Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.'),
  ('due_diligence', '2026.08.1', 'synthesis', 'synthesize', 'Draft the diligence memo from Extract and Analyse outputs only.');

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'agent-chat', '2026.08.1', TRUE, 'active', 'general_chat',
  'Pattern 0 (single inference): one LLM call from host. No tools, no workflow, no memory, no retrieval.',
  'http://agent-runtime:3008/v1/runs', 'agent-chat', NULL, NULL,
  'low_risk_chat', 'lightweight-chat', NULL, 'agent-chat', NULL, NULL, 1, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["hello","hi","chat"]'::jsonb, 0
),
(
  'email_summarize', '2026.08.1', TRUE, 'active', 'summarize_email',
  'Pattern 0 (single inference): one LLM call from host. Summarize the pasted email. Prompt plus output schema. No tools, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-email-summarize', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'email_summarize', 'exec_bullets', 'email_summarize_golden', 1, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 0
),
(
  'chat_session', '2026.08.1', TRUE, 'active', 'chat_session',
  'Pattern 0 (single inference): one LLM call per turn from host. Session conversation memory. No tools, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-chat-session', NULL, NULL,
  'low_risk_chat', 'lightweight-chat', NULL, 'chat_session', NULL, NULL, 1, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["hello","hi","chat"]'::jsonb, 0
),
(
  'agent-policy-qa', '2026.08.1', TRUE, 'active', 'policy_qa',
  'Pattern 0 (single inference): one LLM call from host after catalogue prefetch of policy-engine and product-faq. Prefetch is not packed today. No tools, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-qa', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'agent-policy-qa', 'cited_answer', 'policy_qa_golden', 1, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["policy","procedure","handbook"]'::jsonb, 0
),
(
  'policy_chat', '2026.08.1', TRUE, 'active', 'policy_chat',
  'Pattern 0 (single inference): one LLM call per turn from host. Catalogue prefetch of policy-engine plus session memory. No tools, no workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-chat', NULL, NULL,
  'read_only_standard', 'fast-chat', NULL, 'policy_chat', 'cited_answer', 'policy_qa_golden', 1, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["policy","handbook"]'::jsonb, 0
),
(
  'search_only', '2026.08.1', TRUE, 'active', 'search_only',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over web_search, up to max_loop_steps. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-search-only', 'search_only', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'search_only', NULL, NULL, 8, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["search","google"]'::jsonb, 1
),
(
  'research_assistant', '2026.08.1', TRUE, 'active', 'research_topic',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over web_search, fetch_url, note_store, draft_brief. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-research-assistant', 'research_assistant', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'research_assistant', 'research_brief', 'research_assistant_golden', 16, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["research","sources"]'::jsonb, 1
),
(
  'fraud_one_tool', '2026.08.1', TRUE, 'active', 'fraud_one_tool',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over draft_memo after catalogue prefetch of accounts. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-one-tool', 'fraud_one_tool', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_one_tool', 'risk_memo', NULL, 6, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fraud_casefile', '2026.08.1', TRUE, 'active', 'fraud_casefile',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, risk_engine, draft_memo after catalogue prefetch. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-casefile', 'fraud_casefile', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_casefile', 'risk_memo', NULL, 10, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fee_explain', '2026.08.1', TRUE, 'active', 'fee_explain',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over account_fee_lookup. One host prompt reused each turn. Domain HTTP only on CALL. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain', 'fee_explain', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fee_explain', 'fee_explain_out', 'fee_explain_golden', 6, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["fee","charged","charge","42","monthly"]'::jsonb, 1
),
(
  'contract_investigation', '2026.08.1', TRUE, 'active', 'contract_investigate',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, clause_search, policy_search, risk_engine, draft_memo. One host prompt reused each turn. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-contract-investigate', 'contract_investigate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'contract_investigate', 'risk_memo', 'contract_investigate_golden', 12, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'llm_pipeline', '2026.08.1', TRUE, 'active', 'llm_pipeline',
  'Pattern 2 (deterministic): fixed workflow of three LLM stages. Prompts: host plus classify and synthesis templates. No domain HTTP.',
  'http://agent-runtime:3008/v1/runs', 'agent-llm-pipeline', NULL, NULL,
  'read_only_standard', 'fast-chat', 'llm_pipeline', 'llm_pipeline', NULL, 'llm_pipeline_tools', NULL, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'policy_memo', '2026.08.1', TRUE, 'active', 'policy_memo',
  'Pattern 2 (deterministic): prefetch placeholder then one synthesis call. Prompts: host plus synthesis template. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-policy-memo', NULL, NULL,
  'read_only_standard', 'reasoning-standard', 'policy_memo', 'policy_memo', 'msa_memo', 'policy_memo_tools', NULL, 'clarify',
  '["policy:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'account_notify', '2026.08.1', TRUE, 'active', 'account_notify',
  'Pattern 2 (deterministic): domain HTTP notify_customer, then synthesis confirm. Prompts: host plus synthesis template.',
  'http://agent-runtime:3008/v1/runs', 'agent-account-notify', 'account_notify', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'account_notify', 'account_notify', NULL, 'account_notify_tools', NULL, 'escalate_human',
  '["notify:send"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'card_freeze', '2026.08.1', TRUE, 'active', 'card_freeze',
  'Pattern 2 (deterministic): domain HTTP identity_check, limit_check, freeze_card, then synthesis confirm. Prompts: host plus synthesis template. Freeze remains a gated side effect in catalogue.',
  'http://agent-runtime:3008/v1/runs', 'agent-card-freeze', 'card_freeze', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'card_freeze', 'card_freeze', NULL, 'card_freeze_tools', NULL, 'escalate_human',
  '["cards:freeze"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'dispute_intake', '2026.08.1', TRUE, 'active', 'dispute_intake',
  'Pattern 2 (deterministic): two domain HTTP steps then synthesis on packet_summarize. Prompts: host plus synthesis template.',
  'http://agent-runtime:3008/v1/runs', 'agent-dispute-intake', 'dispute_intake', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'dispute_intake', 'dispute_intake', NULL, 'dispute_intake_tools', NULL, 'clarify',
  '["disputes:write"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'purchase_refund', '2026.08.1', TRUE, 'active', 'purchase_refund',
  'Pattern 2 (deterministic): HTTP OCR, classify receipt JSON, HTTP match and eligibility, gated refund, synthesis confirm. output_schema_id receipt_fields is not enforced. human_gate is catalogue-only. HTTP stays goal-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-purchase-refund', 'purchase_refund', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'purchase_refund', 'purchase_refund', 'receipt_fields', 'purchase_refund_tools', NULL, 'escalate_human',
  '["refunds:write"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_notify', '2026.08.1', TRUE, 'active', 'pack_then_notify',
  'Pattern 2 (deterministic): prefetch placeholder, domain HTTP notify, then synthesis confirm. Prompts: host plus synthesis template. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-notify', 'account_notify', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'pack_then_notify', 'pack_then_notify', NULL, 'pack_then_notify_tools', NULL, 'escalate_human',
  '["notify:send"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_freeze', '2026.08.1', TRUE, 'active', 'pack_then_freeze',
  'Pattern 2 (deterministic): prefetch placeholder, three domain HTTP writes, then synthesis confirm. Prompts: host plus synthesis template. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-freeze', 'card_freeze', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'pack_then_freeze', 'pack_then_freeze', NULL, 'pack_then_freeze_tools', NULL, 'escalate_human',
  '["cards:freeze"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'pack_then_review', '2026.08.1', TRUE, 'active', 'pack_then_review',
  'Pattern 2 (deterministic): prefetch placeholder, two domain HTTP tools, then synthesis memo. Prompts: host plus synthesis template. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-pack-then-review', 'pack_then_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'pack_then_review', 'pack_then_review', 'msa_memo', 'pack_then_review_tools', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'clause_lookup', '2026.08.1', TRUE, 'active', 'clause_lookup',
  'Pattern 2 (deterministic): LLM query_formulation, HTTP clause_search, then synthesis. Prompts: host plus query_formulation and synthesis templates.',
  'http://agent-runtime:3008/v1/runs', 'agent-clause-lookup', 'clause_lookup', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'clause_lookup', 'clause_lookup', NULL, 'clause_lookup_tools', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'template_retrieve', '2026.08.1', TRUE, 'active', 'template_retrieve',
  'Pattern 2 (deterministic): two query_formulation retrieves, HTTP score, then synthesis. Prompts: host plus query_formulation and synthesis templates.',
  'http://agent-runtime:3008/v1/runs', 'agent-template-retrieve', 'template_retrieve', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'template_retrieve', 'template_retrieve', NULL, 'template_retrieve_tools', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'msa_risk_review', '2026.08.1', TRUE, 'active', 'msa_risk_review',
  'Pattern 2 (deterministic): HTTP OCR, two query_formulation retrieves, HTTP score, synthesis memo. Prompts: host plus query_formulation and synthesis templates.',
  'http://agent-runtime:3008/v1/runs', 'agent-msa-risk-review', 'msa_risk_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'msa_risk_review', 'msa_risk_review', 'msa_memo', 'msa_risk_review_tools', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'kyc_onboarding', '2026.08.1', TRUE, 'active', 'kyc_onboard',
  'Pattern 2 (deterministic): domain HTTP KYC tools then synthesis packet. Prompts: host plus synthesis template. branch and human_gate are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-kyc-onboarding', 'kyc_onboarding', '2026.08.1',
  'high_risk_step_up', 'reasoning-standard', 'kyc_onboarding', 'kyc_onboarding', 'kyc_result', 'kyc_onboarding_tools', NULL, 'escalate_human',
  '["kyc:onboard"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'claims_adjudicate', '2026.08.1', TRUE, 'active', 'claims_adjudicate',
  'Pattern 2 (deterministic): HTTP playbook retrieve, query_formulation clause search, HTTP score, synthesis memo. Prompts: host plus query_formulation and synthesis templates.',
  'http://agent-runtime:3008/v1/runs', 'agent-claims-adjudicate', 'claims_adjudicate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'claims_adjudicate', 'claims_adjudicate', 'msa_memo', 'claims_adjudicate_tools', NULL, 'clarify',
  '["claims:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
),
(
  'ticket_triage', '2026.08.1', TRUE, 'active', 'ticket_triage',
  'Pattern 3 (guided): HTTP parse and tag, then synthesis reply. Prompts: host plus synthesis template. Stage allowlists are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-ticket-triage', 'ticket_triage', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'ticket_triage', 'ticket_triage', NULL, NULL, NULL, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'product_explain', '2026.08.1', TRUE, 'active', 'product_explain',
  'Pattern 3 (guided): prefetch placeholder, HTTP score/compare, then synthesis. Prompts: host plus synthesis template. Allowlists are catalogue-only. Prefetch is not packed today.',
  'http://agent-runtime:3008/v1/runs', 'agent-product-explain', 'product_explain', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'product_explain', 'product_explain', NULL, NULL, NULL, 'clarify',
  '["policy:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["loan","offer","product"]'::jsonb, 3
),
(
  'narrow_review', '2026.08.1', TRUE, 'active', 'narrow_review',
  'Pattern 3 (guided): HTTP OCR, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-narrow-review', 'narrow_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'narrow_review', 'narrow_review', 'counsel_memo', NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'contract_review', '2026.08.1', TRUE, 'active', 'contract_review',
  'Pattern 3 (guided): HTTP OCR, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-contract-review', 'contract_review', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'contract_review', 'contract_review', 'counsel_memo', 'contract_review_golden', NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
),
(
  'due_diligence', '2026.08.1', TRUE, 'active', 'due_diligence',
  'Pattern 3 (guided): HTTP playbook extract, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.',
  'http://agent-runtime:3008/v1/runs', 'agent-due-diligence', 'due_diligence', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'due_diligence', 'due_diligence', 'counsel_memo', NULL, NULL, 'clarify',
  '["legal:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 3
);

INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope) VALUES
  ('agent-policy-qa', '2026.08.1', 'deterministic_prefetch', '["policy-engine","product-faq"]'::jsonb),
  ('policy_chat', '2026.08.1', 'deterministic_prefetch', '["policy-engine"]'::jsonb),
  ('fraud_one_tool', '2026.08.1', 'deterministic_prefetch', '["accounts"]'::jsonb),
  ('fraud_casefile', '2026.08.1', 'deterministic_prefetch', '["accounts"]'::jsonb),
  ('fee_explain', '2026.08.1', 'tool', '["accounts"]'::jsonb),
  ('contract_investigation', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('policy_memo', '2026.08.1', 'deterministic_prefetch', '["policy-engine"]'::jsonb),
  ('pack_then_notify', '2026.08.1', 'deterministic_prefetch', '["product-terms"]'::jsonb),
  ('pack_then_freeze', '2026.08.1', 'deterministic_prefetch', '["product-terms"]'::jsonb),
  ('pack_then_review', '2026.08.1', 'deterministic_prefetch', '["legal-playbook"]'::jsonb),
  ('clause_lookup', '2026.08.1', 'tool', '["clause-index"]'::jsonb),
  ('template_retrieve', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('msa_risk_review', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('kyc_onboarding', '2026.08.1', 'tool', '["sanctions-lists","kyc-policy"]'::jsonb),
  ('claims_adjudicate', '2026.08.1', 'tool', '["legal-playbook","clause-index"]'::jsonb),
  ('product_explain', '2026.08.1', 'deterministic_prefetch', '["product-terms","fee-schedule"]'::jsonb),
  ('narrow_review', '2026.08.1', 'tool', '["clause-index"]'::jsonb),
  ('contract_review', '2026.08.1', 'tool', '["clause-index","legal-playbook"]'::jsonb),
  ('due_diligence', '2026.08.1', 'tool', '["legal-playbook","clause-index"]'::jsonb);

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('chat_session', '2026.08.1', 'session', 'session', 'none', 'none', 24, '["tenant","user","session"]'::jsonb),
  ('policy_chat', '2026.08.1', 'session', 'session', 'none', 'none', 24, '["tenant","user","session"]'::jsonb),
  ('search_only', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('research_assistant', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('fraud_one_tool', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('fraud_casefile', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('fee_explain', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('contract_investigation', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('dispute_intake', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('purchase_refund', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('pack_then_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('msa_risk_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('kyc_onboarding', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb),
  ('claims_adjudicate', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('ticket_triage', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('product_explain', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('narrow_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('contract_review', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('due_diligence', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb);
-- Two Pattern 1 parents that name kind=agent. Child jobs POST is catalogue-only.
-- ON CONFLICT: local volumes may already have these rows from seed-db.sh.
INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'fraud_investigate', '2026.08.1', 'Fraud parent: domain OCR/memo plus Legal agent capability',
  $$[
    {"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
    {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"},
    {"name":"start_contract_review","capability_id":"start_contract_review","capability_version":"1.0.0","pdp_action":"start_contract_review","risk_tier":"high"}
  ]$$::jsonb,
  'published'
),
(
  'ops_start_kyc', '2026.08.1', 'Ops parent: parse ticket plus KYC agent capability',
  $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"start_kyc_onboarding","capability_id":"start_kyc_onboarding","capability_version":"1.0.0","pdp_action":"start_kyc_onboarding","risk_tier":"high"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO NOTHING;

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
  ('fraud_investigate', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use OCR and memo tools. You may CALL start_contract_review. Do not invent tools.', 'published', 'fraud-ops'),
  ('ops_start_kyc', '2026.08.1', 'Pattern 1. Reply CALL <tool_id> or DONE <answer>. Parse the ticket. You may CALL start_kyc_onboarding. Do not invent tools.', 'published', 'ops')
ON CONFLICT (prompt_id, prompt_version) DO NOTHING;

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'fraud_investigate', '2026.08.1', TRUE, 'active', 'fraud_investigate',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, draft_memo, start_contract_review. One host prompt reused each turn. kind=agent child start is catalogue-only. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-fraud-investigate', 'fraud_investigate', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fraud_investigate', 'risk_memo', NULL, 8, 'clarify',
  '["fraud:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'ops_start_kyc', '2026.08.1', TRUE, 'active', 'ops_start_kyc',
  'Pattern 1 (autonomous): LLM CALL/DONE loop over parse_ticket and start_kyc_onboarding. One host prompt reused each turn. kind=agent child start is catalogue-only. No workflow.',
  'http://agent-runtime:3008/v1/runs', 'agent-ops-start-kyc', 'ops_start_kyc', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'ops_start_kyc', NULL, NULL, 6, 'clarify',
  '["kyc:onboard"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 1
)
ON CONFLICT (route_id, route_version) DO NOTHING;

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('fraud_investigate', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('ops_start_kyc', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user","session"]'::jsonb)
ON CONFLICT (route_id, route_version) DO NOTHING;
