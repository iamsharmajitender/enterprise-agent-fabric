-- overdraft_fee_qa — banking corpora (dedicated search URLs on agent-mocks).

\c adp
INSERT INTO dataplane.corpora (
  corpus_id, display_name, url, collection, auth, owner, status, region
) VALUES
(
  'fee-schedule', 'Fee schedule',
  'http://agent-mocks:3010/corpora/fee-schedule/search',
  'fee-schedule', 'workload-oauth', 'product', 'published', NULL
),
(
  'product-disclosure', 'Product disclosure statements',
  'http://agent-mocks:3010/corpora/product-disclosure/search',
  'product-disclosure', 'workload-oauth', 'product', 'published', NULL
)
ON CONFLICT (corpus_id) DO UPDATE SET
  display_name = EXCLUDED.display_name,
  url = EXCLUDED.url,
  collection = EXCLUDED.collection,
  status = EXCLUDED.status,
  updated_at = now();
