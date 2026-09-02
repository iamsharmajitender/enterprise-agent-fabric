-- billing_assistant — remove catalogue rows for this route pack (shared capabilities are kept).

\c adp
DELETE FROM dataplane.retrieval WHERE route_id = 'billing_assistant';
DELETE FROM dataplane.memory_profiles WHERE route_id = 'billing_assistant';
DELETE FROM dataplane.routes WHERE route_id = 'billing_assistant';
DELETE FROM dataplane.prompt_packs WHERE prompt_id = 'billing_assistant';
DELETE FROM dataplane.manifests WHERE manifest_id = 'billing_assistant';

\c acr
DELETE FROM registry.manifests WHERE manifest_id = 'billing_assistant';
