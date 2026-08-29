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

-- ShopAssist case route catalogue seed.

INSERT INTO dataplane.manifests (
  manifest_id, manifest_version, description, tools, status
) VALUES
(
  'shopassist_case', '2026.08.1', 'ShopAssist front-line support: ASK for a locator, lookup order, billing/policy domain APIs, escalate',
  $$[
    {"name":"lookup_order","capability_id":"lookup_order","capability_version":"1.0.0","pdp_action":"lookup_order","risk_tier":"low"},
    {"name":"lookup_order_by_customer","capability_id":"lookup_order_by_customer","capability_version":"1.0.0","pdp_action":"lookup_order_by_customer","risk_tier":"low"},
    {"name":"lookup_order_by_email","capability_id":"lookup_order_by_email","capability_version":"1.0.0","pdp_action":"lookup_order_by_email","risk_tier":"low"},
    {"name":"investigate_duplicate_charge","capability_id":"investigate_duplicate_charge","capability_version":"1.0.0","pdp_action":"investigate_duplicate_charge","risk_tier":"low"},
    {"name":"check_return_policy","capability_id":"check_return_policy","capability_version":"1.0.0","pdp_action":"check_return_policy","risk_tier":"low"},
    {"name":"escalate_to_human","capability_id":"escalate_to_human","capability_version":"1.0.0","pdp_action":"escalate_to_human","risk_tier":"high"}
  ]$$::jsonb,
  'published'
);

INSERT INTO dataplane.prompt_packs (
  prompt_id, prompt_version, host, status, owner
) VALUES
('shopassist_case', '2026.08.1', 'Pattern 1. You are ShopAssist front-line support. Reply CALL <tool_id>, ASK <question>, or DONE <answer>. Extract facts from the customer text yourself. If they have not given an order id, customer id, or email, ASK for one of those. When prior notes include customer: <value>, treat that as the locator they just sent: ORD-* → CALL lookup_order with {"order_id":...}, CUS-* → CALL lookup_order_by_customer with {"customer_id":...}, email → CALL lookup_order_by_email with {"email":...}. When the locator is already in the goal or notes, CALL the matching lookup with JSON on the next line. Domain tools never receive the utterance. After order details, CALL investigate_duplicate_charge when the customer reports a double charge or duplicate billing. CALL check_return_policy when they ask for a refund or report damage; pass order_id and item_id from the lookup result. CALL escalate_to_human when policy recommends escalation, the refund exceeds the automatic limit, or the customer insists on a full refund review. After escalate_to_human succeeds, DONE immediately with a customer-facing summary that includes the handoff id — never CALL escalate_to_human twice. If policy approves automatic store credit and the customer accepted it, DONE with the resolution. Do not invent tool results.', 'published', 'shopassist');

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'shopassist_case', '2026.08.1', TRUE, 'active', 'shopassist_case',
  'Pattern 1 (autonomous): ShopAssist front-line support. ASK for order/customer/email if missing, lookup order, then billing and policy domain APIs. Escalate when needed.',
  'http://agent-runtime:3008/v1/runs', 'agent-shopassist-case', 'shopassist_case', '2026.08.1',
  'read_only_standard', 'reasoning-standard', NULL, 'shopassist_case', NULL, NULL, 12, 'clarify',
  '["support:case"]'::jsonb, '["web","api"]'::jsonb, TRUE, '["damaged","damage","refund","jacket","charged twice","duplicate charge","ORD-77819"]'::jsonb, 1
);

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
('shopassist_case', '2026.08.1', 'session', 'session', 'checkpoint', 'none', 24, '["tenant","user","session"]'::jsonb);
