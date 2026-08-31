-- fee_explain — remove catalogue rows for this route pack.

\c adp
DELETE FROM dataplane.retrieval WHERE route_id = 'fee_explain';
DELETE FROM dataplane.memory_profiles WHERE route_id = 'fee_explain';
DELETE FROM dataplane.routes WHERE route_id = 'fee_explain';
DELETE FROM dataplane.prompt_packs WHERE prompt_id = 'fee_explain';
DELETE FROM dataplane.manifests WHERE manifest_id = 'fee_explain';

\c acr
DELETE FROM registry.manifests WHERE manifest_id = 'fee_explain';
DELETE FROM registry.capabilities WHERE id = 'account_fee_lookup';
