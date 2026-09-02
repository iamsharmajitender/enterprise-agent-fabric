-- ticket_triage — tool manifest (ACR publish + ADP catalogue copy).

\c acr
INSERT INTO registry.manifests (
  manifest_id, manifest_version, tools, status
) VALUES
(
  'ticket_triage', '2026.08.1', $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"tag_intent","capability_id":"tag_intent","capability_version":"1.0.0","pdp_action":"tag_intent","risk_tier":"low"},
    {"name":"draft_reply","capability_id":"draft_reply","capability_version":"1.0.0","pdp_action":"draft_reply","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO UPDATE SET
  tools = EXCLUDED.tools,
  status = EXCLUDED.status;

\c adp
INSERT INTO dataplane.manifests (
  manifest_id, manifest_version, description, tools, status
) VALUES
(
  'ticket_triage', '2026.08.1',
  'Pattern 3 guided triage: parse ticket, tag intent (reads parse slot), start ticket_draft_reply child agent (kind=agent join). Stage allowlists are catalogue-only until inner loop ships.',
  $$[
    {"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
    {"name":"tag_intent","capability_id":"tag_intent","capability_version":"1.0.0","pdp_action":"tag_intent","risk_tier":"low"},
    {"name":"draft_reply","capability_id":"draft_reply","capability_version":"1.0.0","pdp_action":"draft_reply","risk_tier":"medium"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (manifest_id, manifest_version) DO UPDATE SET
  description = EXCLUDED.description,
  tools = EXCLUDED.tools,
  status = EXCLUDED.status;
