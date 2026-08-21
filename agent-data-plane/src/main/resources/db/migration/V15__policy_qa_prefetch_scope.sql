UPDATE dataplane.retrieval
   SET scope = '["policy-engine","product-faq"]'::jsonb
 WHERE route_id = 'agent-policy-qa-v1'
   AND route_version = '2026.08.1';
