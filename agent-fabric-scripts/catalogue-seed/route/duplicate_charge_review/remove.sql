-- duplicate_charge_review — remove catalogue rows for this route pack.

\c adp
DELETE FROM dataplane.routes WHERE route_id = 'duplicate_charge_review';
DELETE FROM dataplane.workflows WHERE workflow_id = 'duplicate_charge_review';
DELETE FROM dataplane.prompt_role_templates WHERE prompt_id = 'duplicate_charge_review';
DELETE FROM dataplane.prompt_packs WHERE prompt_id = 'duplicate_charge_review';
DELETE FROM dataplane.manifests WHERE manifest_id = 'duplicate_charge_review';

\c acr
DELETE FROM registry.manifests WHERE manifest_id = 'duplicate_charge_review';
DELETE FROM registry.capabilities WHERE id IN ('duplicate_charge_intake', 'duplicate_charge_respond');
