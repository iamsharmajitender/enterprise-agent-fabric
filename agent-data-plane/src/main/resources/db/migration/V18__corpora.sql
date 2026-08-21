CREATE TABLE dataplane.corpora (
  corpus_id     text PRIMARY KEY,
  display_name  text NOT NULL,
  url           text NOT NULL,
  collection    text,
  auth          text NOT NULL DEFAULT 'workload-oauth',
  owner         text NOT NULL,
  status        text NOT NULL CHECK (status IN ('draft', 'published', 'deprecated')),
  region        text,
  updated_at    timestamptz NOT NULL DEFAULT now()
);

INSERT INTO dataplane.corpora (
  corpus_id, display_name, url, collection, auth, owner, status, region
) VALUES
(
  'policy-engine',
  'Policy engine',
  'https://retrieve.internal/v1/search',
  'policy-engine',
  'workload-oauth',
  'policy-ops',
  'published',
  NULL
),
(
  'clause-index',
  'Clause index',
  'https://retrieve.internal/v1/search',
  'clause-index',
  'workload-oauth',
  'legal',
  'published',
  NULL
),
(
  'legal-playbook',
  'Legal playbook',
  'https://retrieve.internal/v1/search',
  'legal-playbook',
  'workload-oauth',
  'legal',
  'published',
  NULL
),
(
  'product-faq',
  'Product FAQ',
  'https://retrieve.internal/v1/search',
  'product-faq',
  'workload-oauth',
  'assistant-platform',
  'published',
  NULL
),
(
  'accounts',
  'Accounts',
  'https://retrieve.internal/v1/search',
  'accounts',
  'workload-oauth',
  'assistant-platform',
  'published',
  NULL
),
(
  'sanctions-lists',
  'Sanctions lists',
  'https://retrieve.internal/v1/search',
  'sanctions-lists',
  'workload-oauth',
  'kyc-ops',
  'published',
  NULL
),
(
  'kyc-policy',
  'KYC policy',
  'https://retrieve.internal/v1/search',
  'kyc-policy',
  'workload-oauth',
  'kyc-ops',
  'published',
  NULL
),
(
  'research-index',
  'Research index',
  'https://retrieve.internal/v1/search',
  'research-index',
  'workload-oauth',
  'assistant-platform',
  'draft',
  NULL
);
