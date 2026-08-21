ALTER TABLE dataplane.routes
  ADD COLUMN status TEXT NOT NULL DEFAULT 'published';

UPDATE dataplane.routes SET status = 'active' WHERE active = TRUE;

ALTER TABLE dataplane.routes
  ADD CONSTRAINT routes_status_chk
    CHECK (status IN ('draft', 'published', 'active', 'retired')),
  ADD CONSTRAINT routes_status_active_chk
    CHECK ((active AND status = 'active') OR (NOT active AND status <> 'active'));

UPDATE dataplane.routes
   SET status = 'retired'
 WHERE route_id = 'fee_explain' AND route_version = '2026.04.1';

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords
) VALUES (
  'agent-research-v0',
  '2026.08.1',
  FALSE,
  'draft',
  'research_draft',
  'Draft research worker, not yet live',
  NULL,
  'agent-research-v0',
  NULL,
  NULL,
  'read_only_standard',
  'lightweight-chat',
  NULL,
  'research_v0',
  NULL,
  NULL,
  4,
  'clarify',
  '[]'::jsonb,
  '["web"]'::jsonb,
  FALSE,
  '[]'::jsonb
);

ALTER TABLE dataplane.manifests
  ADD COLUMN status TEXT NOT NULL DEFAULT 'published';

ALTER TABLE dataplane.manifests
  ADD CONSTRAINT manifests_status_chk
    CHECK (status IN ('draft', 'published', 'retired'));

INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'fee_explain_v1',
  '2026.07.1',
  'Look up why an account fee was charged',
  $$[
    {
      "name": "account_fee_lookup",
      "capability_id": "account_fee_lookup",
      "capability_version": "1.0.0",
      "pdp_action": "account_fee_lookup",
      "risk_tier": "low"
    }
  ]$$::jsonb,
  'published'
),
(
  'research_tools_v0',
  '2026.08.1',
  'Draft research tools, not live',
  '[]'::jsonb,
  'draft'
),
(
  'fax_lookup_v0',
  '2026.04.1',
  'Retired fax lookup tools',
  '[]'::jsonb,
  'retired'
);

DROP INDEX IF EXISTS dataplane.prompt_packs_one_published;

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
(
  'fee_explain_v1',
  '2026.07.1',
  'You explain account fees. Use the fee lookup tool.',
  'published',
  'assistant-platform'
),
(
  'research_v0',
  '2026.08.1',
  'Draft research host. Not published.',
  'draft',
  'assistant-platform'
);
