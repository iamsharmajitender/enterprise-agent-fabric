-- overdraft_fee_qa — deterministic prefetch over fee schedule + product disclosure corpora.

\c adp
INSERT INTO dataplane.retrieval (
  route_id, route_version, mode, scope
) VALUES
(
  'overdraft_fee_qa', '2026.08.1', 'deterministic_prefetch',
  '["fee-schedule","product-disclosure"]'::jsonb
)
ON CONFLICT (route_id, route_version) DO NOTHING;
