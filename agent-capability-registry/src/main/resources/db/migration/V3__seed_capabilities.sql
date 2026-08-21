ALTER TABLE registry.capabilities
  ALTER COLUMN output_schema DROP NOT NULL;

INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'ocr_extract',
  '1.2.0',
  'domain',
  'Extract text from a document id.',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/ocr/extract","auth":"domain-oauth"}'::jsonb,
  NULL,
  'document-intel',
  'published'
),
(
  'start_contract_review',
  '1.0.0',
  'agent_start',
  'Start governed Legal MSA review as a jobs run.',
  '{"type":"object","required":["document_id"],"properties":{"document_id":{"type":"string"},"matter_id":{"type":"string"}}}'::jsonb,
  NULL,
  '{"method":"POST","url":"https://api-afd.internal/v1/jobs","auth":"calling-agent-oauth","body":{"route_id":"contract_review"}}'::jsonb,
  NULL,
  'legal-agents',
  'published'
),
(
  'search_transactions',
  '1.4.0',
  'domain',
  'Search transactions for fraud investigation.',
  '{"type":"object","required":["account_id"],"properties":{"account_id":{"type":"string"},"from":{"type":"string"},"to":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["transactions"],"properties":{"transactions":{"type":"array"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/transactions/search","auth":"domain-oauth"}'::jsonb,
  NULL,
  'fraud-ops',
  'published'
)
ON CONFLICT (id, version) DO NOTHING;
