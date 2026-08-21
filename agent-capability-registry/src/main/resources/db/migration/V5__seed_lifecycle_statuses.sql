INSERT INTO registry.capabilities (
  id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
) VALUES
(
  'ocr_extract',
  '1.1.0',
  'domain',
  'Extract text from a document id (superseded).',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/ocr/extract","auth":"domain-oauth"}'::jsonb,
  NULL,
  'document-intel',
  'published'
),
(
  'invoice_intake',
  '0.1.0',
  'domain',
  'Draft invoice intake extractor, not published.',
  '{"type":"object","required":["doc_id"],"properties":{"doc_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["fields"],"properties":{"fields":{"type":"object"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/invoices/intake","auth":"domain-oauth"}'::jsonb,
  NULL,
  'document-intel',
  'draft'
),
(
  'fax_ocr_legacy',
  '0.9.0',
  'domain',
  'Retired fax OCR. Do not activate again.',
  '{"type":"object","required":["fax_id"],"properties":{"fax_id":{"type":"string"}}}'::jsonb,
  '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}'::jsonb,
  '{"method":"POST","url":"https://api.internal/ocr/fax","auth":"domain-oauth"}'::jsonb,
  NULL,
  'document-intel',
  'retired'
)
ON CONFLICT (id, version) DO NOTHING;
