INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'account-balance-v1',
  '2026.08.1',
  'List accounts to answer a cleared-balance question',
  $$[
    {
      "name": "list_accounts",
      "capability_id": "list_accounts",
      "capability_version": "1.0.0",
      "pdp_action": "list_accounts",
      "risk_tier": "low"
    }
  ]$$::jsonb,
  'published'
),
(
  'account-statement-v1',
  '2026.08.1',
  'List accounts and transactions for a statement pack',
  $$[
    {
      "name": "list_accounts",
      "capability_id": "list_accounts",
      "capability_version": "1.0.0",
      "pdp_action": "list_accounts",
      "risk_tier": "low"
    },
    {
      "name": "list_transactions",
      "capability_id": "list_transactions",
      "capability_version": "1.0.0",
      "pdp_action": "list_transactions",
      "risk_tier": "low"
    }
  ]$$::jsonb,
  'published'
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
(
  'account_balance_v1',
  '2026.08.1',
  'Answer cleared-balance questions. Use list_accounts only.',
  'published',
  'assistant-platform'
),
(
  'account_statement_v1',
  '2026.08.1',
  'Assemble a statement pack. Use list_accounts and list_transactions. Do not initiate payments.',
  'published',
  'assistant-platform'
);

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords
) VALUES
(
  'agent-balance-v1',
  '2026.08.1',
  TRUE,
  'active',
  'account_balance',
  'Cleared balance via list_accounts',
  NULL,
  'agent-balance-v1',
  'account-balance-v1',
  '2026.08.1',
  'read_only_standard',
  'reasoning-standard',
  NULL,
  'account_balance_v1',
  NULL,
  NULL,
  4,
  'clarify',
  '["accounts:read"]'::jsonb,
  '["web"]'::jsonb,
  TRUE,
  '["cleared-funds","available-balance","ledger-balance"]'::jsonb
),
(
  'agent-statement-v1',
  '2026.08.1',
  TRUE,
  'active',
  'account_statement',
  'Statement pack via list_accounts and list_transactions',
  NULL,
  'agent-statement-v1',
  'account-statement-v1',
  '2026.08.1',
  'read_only_standard',
  'reasoning-standard',
  NULL,
  'account_statement_v1',
  NULL,
  NULL,
  5,
  'clarify',
  '["accounts:read"]'::jsonb,
  '["web"]'::jsonb,
  TRUE,
  '["e-statement","pdf-statement","tax-pack"]'::jsonb
);

INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope) VALUES
  ('agent-balance-v1', '2026.08.1', 'tool', '["accounts"]'::jsonb),
  ('agent-statement-v1', '2026.08.1', 'tool', '["accounts"]'::jsonb);

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('agent-balance-v1', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('agent-statement-v1', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb);
