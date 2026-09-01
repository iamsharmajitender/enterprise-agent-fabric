-- ticket_triage — remove catalogue rows for this route pack.

\c adp
DELETE FROM dataplane.memory_profiles WHERE route_id = 'ticket_triage';
DELETE FROM dataplane.routes WHERE route_id = 'ticket_triage';
DELETE FROM dataplane.workflows WHERE workflow_id = 'ticket_triage';
DELETE FROM dataplane.prompt_role_templates WHERE prompt_id = 'ticket_triage';
DELETE FROM dataplane.prompt_packs WHERE prompt_id = 'ticket_triage';
DELETE FROM dataplane.manifests WHERE manifest_id = 'ticket_triage';

\c acr
DELETE FROM registry.manifests WHERE manifest_id = 'ticket_triage';
DELETE FROM registry.capabilities WHERE id IN ('parse_ticket', 'tag_intent', 'draft_reply');
