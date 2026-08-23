-- Extra catalogue cuts: published / draft / retired (or deprecated) for each type,
-- plus extra versions so History pages have something to compare.
-- Run after create-seed-data.sql via ./docs/run/scripts/seed-db.sh.

\c acr

-- Capabilities: history on seed ids, plus standalone draft / retired / published.
INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'ocr_extract', '1.0.0', 'domain',
  'Extract text from a document id (first cut, retired).',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/ocr/extract","auth":"domain-oauth"}'::jsonb,
  NULL, 'document-intel', 'retired'
),
(
  'ocr_extract', '1.1.0', 'domain',
  'Extract text from a document id (superseded published cut).',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/ocr/extract","auth":"domain-oauth"}'::jsonb,
  NULL, 'document-intel', 'published'
),
(
  'web_search', '0.9.0', 'domain',
  'Search the public web (retired prototype).',
  '{"type":"object","required":["query"],"properties":{"query":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/search/web","auth":"domain-oauth"}'::jsonb,
  NULL, 'assistant-platform', 'retired'
),
(
  'web_search', '1.1.0', 'domain',
  'Search the public web (draft next cut).',
  '{"type":"object","required":["query"],"properties":{"query":{"type":"string"},"site":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/search/web","auth":"domain-oauth"}'::jsonb,
  NULL, 'assistant-platform', 'draft'
),
(
  'invoice_intake', '0.1.0', 'domain',
  'Draft invoice intake extractor, not published.',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["fields"],"properties":{"fields":{"type":"object"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/invoices/intake","auth":"domain-oauth"}'::jsonb,
  NULL, 'document-intel', 'draft'
),
(
  'fax_ocr_legacy', '0.9.0', 'domain',
  'Retired fax OCR. Do not activate again.',
  '{"type":"object","required":["fax_id"],"properties":{"fax_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/ocr/fax","auth":"domain-oauth"}'::jsonb,
  NULL, 'document-intel', 'retired'
),
(
  'credit_limit_lookup', '1.0.0', 'domain',
  'Look up the entitled credit limit for an account. Not wired to a manifest yet.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["limit"],"properties":{"limit":{"type":"number"},"currency":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"http://tool-mock:3010/credit/limit","auth":"domain-oauth"}'::jsonb,
  NULL, 'lending', 'published'
);

INSERT INTO registry.manifests (manifest_id, manifest_version, tools, status) VALUES
(
  'fee_explain', '2026.04.1',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'fee_explain', '2026.07.1',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'search_only', '2026.09.1',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.1.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'draft'
),
(
  'research_tools', '2026.08.1',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'draft'
),
(
  'fax_lookup', '2026.04.1',
  '[{"name":"fax_ocr_legacy","capability_id":"fax_ocr_legacy","capability_version":"0.9.0","pdp_action":"fax_ocr","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'credit_lookup', '2026.08.1',
  '[{"name":"credit_limit_lookup","capability_id":"credit_limit_lookup","capability_version":"1.0.0","pdp_action":"credit_limit_lookup","risk_tier":"low"}]'::jsonb,
  'published'
);

\c adp

INSERT INTO dataplane.corpora (
  corpus_id, display_name, url, collection, auth, owner, status, region
) VALUES
  ('credit-policy', 'Credit policy', 'https://retrieve.internal/v1/search', 'credit-policy', 'workload-oauth', 'lending', 'published', NULL),
  ('research-notes', 'Research notes', 'https://retrieve.internal/v1/search', 'research-notes', 'workload-oauth', 'assistant-platform', 'draft', NULL),
  ('fax-archive', 'Fax archive', 'https://retrieve.internal/v1/search', 'fax-archive', 'workload-oauth', 'document-intel', 'deprecated', NULL);

INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools, status) VALUES
(
  'fee_explain', '2026.04.1', 'One retrieve tool for account fees (retired cut)',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'fee_explain', '2026.07.1', 'One retrieve tool for account fees (published, not live)',
  '[{"name":"account_fee_lookup","capability_id":"account_fee_lookup","capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]'::jsonb,
  'published'
),
(
  'search_only', '2026.09.1', 'One web search tool (draft next cut)',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.1.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'draft'
),
(
  'research_tools', '2026.08.1', 'Draft research tools, not live',
  '[{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"}]'::jsonb,
  'draft'
),
(
  'fax_lookup', '2026.04.1', 'Retired fax lookup tools',
  '[{"name":"fax_ocr_legacy","capability_id":"fax_ocr_legacy","capability_version":"0.9.0","pdp_action":"fax_ocr","risk_tier":"low"}]'::jsonb,
  'retired'
),
(
  'credit_lookup', '2026.08.1', 'One credit-limit retrieve tool',
  '[{"name":"credit_limit_lookup","capability_id":"credit_limit_lookup","capability_version":"1.0.0","pdp_action":"credit_limit_lookup","risk_tier":"low"}]'::jsonb,
  'published'
);

-- Older workflow versions cannot be published (one published per id).
INSERT INTO dataplane.workflows (workflow_id, workflow_version, description, stages, status) VALUES
(
  'llm_pipeline', '2026.04.1', 'Fixed LLM stages (retired first cut)',
  '[{"id":"extract","llm_role":"classify"},{"id":"format","llm_role":"synthesis"}]'::jsonb,
  'deprecated'
),
(
  'llm_pipeline', '2026.09.1', 'Fixed LLM stages (draft next cut)',
  '[{"id":"extract","llm_role":"classify"},{"id":"rewrite","llm_role":"synthesis"},{"id":"format","llm_role":"synthesis"}]'::jsonb,
  'draft'
),
(
  'contract_review', '2026.04.1', 'Extract → report only (retired)',
  '[{"id":"extract","tool":"ocr_extract","llm_role":"none"},{"id":"report","tool":"draft_memo","llm_role":"synthesis"}]'::jsonb,
  'deprecated'
),
(
  'research_draft', '2026.08.1', 'Draft research stages, not published',
  '[{"id":"search","tool":"web_search","llm_role":"none"}]'::jsonb,
  'draft'
),
(
  'fax_pipeline', '2026.04.1', 'Retired fax OCR pipeline',
  '[{"id":"ocr","tool":"fax_ocr_legacy","llm_role":"none"}]'::jsonb,
  'deprecated'
),
(
  'credit_check', '2026.08.1', 'Look up entitled credit limit',
  '[{"id":"lookup","tool":"credit_limit_lookup","llm_role":"none"}]'::jsonb,
  'published'
);

INSERT INTO dataplane.prompt_packs (prompt_id, prompt_version, host, status, owner) VALUES
  ('fee_explain', '2026.04.1', 'Look up why an account fee posted.', 'deprecated', 'assistant-platform'),
  ('fee_explain', '2026.07.1', 'You explain account fees. Use the fee lookup tool.', 'published', 'assistant-platform'),
  ('llm_pipeline', '2026.04.1', 'Do only the current stage. Do not choose the next stage. No tools.', 'deprecated', 'assistant-platform'),
  ('llm_pipeline', '2026.09.1', 'Do only the current stage. Draft next host. No tools.', 'draft', 'assistant-platform'),
  ('agent-chat', '2026.09.1', 'Be a concise corporate assistant. Draft next host.', 'draft', 'assistant-platform'),
  ('research_v0', '2026.08.1', 'Draft research host. Not published.', 'draft', 'assistant-platform'),
  ('fax_summarize', '2026.04.1', 'Summarize a fax. Retired.', 'deprecated', 'document-intel'),
  ('credit_explain', '2026.08.1', 'Explain the entitled credit limit. Do not invent numbers.', 'published', 'lending');

INSERT INTO dataplane.prompt_role_templates (prompt_id, prompt_version, llm_role, task_type, "text") VALUES
  ('llm_pipeline', '2026.04.1', 'classify', 'classify', 'Extract the requested fields from the input only.'),
  ('llm_pipeline', '2026.04.1', 'synthesis', 'synthesize', 'Format using the previous stage output only.'),
  ('llm_pipeline', '2026.09.1', 'classify', 'classify', 'Extract the requested fields from the input only.'),
  ('llm_pipeline', '2026.09.1', 'synthesis', 'synthesize', 'Rewrite or format using the previous stage output only.');

INSERT INTO dataplane.routes (
  route_id, route_version, active, status, intent_label, description,
  activation_target, agent_client_id, tool_manifest, tool_manifest_version,
  policy_profile, model_profile, workflow_id, prompt_id, output_schema_id,
  eval_suite_id, max_loop_steps, fallback, required_claims, channels,
  chat_visible, keywords, autonomy_mode
) VALUES
(
  'fee_explain', '2026.04.1', FALSE, 'retired', 'fee_explain',
  'Look up a charged fee (retired cut).',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain', 'fee_explain', '2026.04.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fee_explain', 'fee_explain_out', NULL, 3, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["fee","charged"]'::jsonb, 1
),
(
  'fee_explain', '2026.07.1', FALSE, 'published', 'fee_explain',
  'Explain an account fee (published, not the live contestant).',
  'http://agent-runtime:3008/v1/runs', 'agent-fee-explain', 'fee_explain', '2026.07.1',
  'read_only_standard', 'reasoning-standard', NULL, 'fee_explain', 'fee_explain_out', 'fee_explain_golden', 5, 'clarify',
  '["accounts:read"]'::jsonb, '["web"]'::jsonb, TRUE, '["fee","charged","charge"]'::jsonb, 1
),
(
  'search_only', '2026.09.1', FALSE, 'draft', 'search_only',
  'Open loop with one tool (draft next cut).',
  'http://agent-runtime:3008/v1/runs', 'agent-search-only', 'search_only', '2026.09.1',
  'read_only_standard', 'reasoning-standard', NULL, 'search_only', NULL, NULL, 8, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["search","google"]'::jsonb, 1
),
(
  'agent-chat', '2026.07.1', FALSE, 'published', 'general_chat',
  'One LLM call. Prompt only (published, not live).',
  'http://agent-runtime:3008/v1/runs', 'agent-chat', NULL, NULL,
  'low_risk_chat', 'lightweight-chat', NULL, 'agent-chat', NULL, NULL, 1, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, TRUE, '["hello","hi","chat"]'::jsonb, 0
),
(
  'research_draft', '2026.08.1', FALSE, 'draft', 'research_draft',
  'Draft research worker, not yet live.',
  NULL, 'agent-research-v0', 'research_tools', '2026.08.1',
  'read_only_standard', 'lightweight-chat', NULL, 'research_v0', NULL, NULL, 4, 'clarify',
  '[]'::jsonb, '["web"]'::jsonb, FALSE, '[]'::jsonb, 1
),
(
  'fax_lookup', '2026.04.1', FALSE, 'retired', 'fax_lookup',
  'Retired fax lookup. Do not activate again.',
  'http://agent-runtime:3008/v1/runs', 'agent-fax-lookup', 'fax_lookup', '2026.04.1',
  'read_only_standard', 'fast-chat', NULL, 'fax_summarize', NULL, NULL, 2, 'clarify',
  '[]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 0
),
(
  'credit_explain', '2026.08.1', FALSE, 'published', 'credit_explain',
  'Published credit-limit explain. Not the live contestant.',
  'http://agent-runtime:3008/v1/runs', 'agent-credit-explain', 'credit_lookup', '2026.08.1',
  'read_only_standard', 'reasoning-standard', 'credit_check', 'credit_explain', NULL, NULL, 4, 'clarify',
  '["accounts:read"]'::jsonb, '["api"]'::jsonb, FALSE, '[]'::jsonb, 2
);

INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope) VALUES
  ('fee_explain', '2026.04.1', 'tool', '["accounts"]'::jsonb),
  ('fee_explain', '2026.07.1', 'tool', '["accounts"]'::jsonb),
  ('credit_explain', '2026.08.1', 'tool', '["credit-policy"]'::jsonb);

INSERT INTO dataplane.memory_profiles (
  route_id, route_version, conversation, working, "loop", long_term, ttl_hours, isolation
) VALUES
  ('fee_explain', '2026.04.1', 'session', 'session', 'checkpoint', 'none', 8, '["tenant","user"]'::jsonb),
  ('fee_explain', '2026.07.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('search_only', '2026.09.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb),
  ('research_draft', '2026.08.1', 'session', 'session', 'checkpoint', 'retrieve_only', 24, '["tenant","user","session"]'::jsonb);
