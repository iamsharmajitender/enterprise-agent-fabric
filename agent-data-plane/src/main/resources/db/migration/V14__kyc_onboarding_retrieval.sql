INSERT INTO dataplane.retrieval (route_id, route_version, mode, scope)
VALUES (
  'kyc_onboarding',
  '2026.08.1',
  'tool',
  '["sanctions-lists","kyc-policy"]'::jsonb
);
