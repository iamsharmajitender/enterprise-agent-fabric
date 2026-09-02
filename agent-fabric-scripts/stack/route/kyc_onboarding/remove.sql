-- kyc_onboarding — remove catalogue rows for this route pack.

\c adp
DELETE FROM dataplane.routes WHERE route_id = 'kyc_onboarding';
DELETE FROM dataplane.workflows WHERE workflow_id = 'kyc_onboarding';
DELETE FROM dataplane.prompt_role_templates WHERE prompt_id = 'kyc_onboarding';
DELETE FROM dataplane.prompt_packs WHERE prompt_id = 'kyc_onboarding';
DELETE FROM dataplane.manifests WHERE manifest_id = 'kyc_onboarding';

\c acr
DELETE FROM registry.manifests WHERE manifest_id = 'kyc_onboarding';
DELETE FROM registry.capabilities WHERE id IN (
  'kyc_doc_intake',
  'kyc_id_verify',
  'kyc_sanctions_api',
  'kyc_risk_engine',
  'kyc_account_activate'
);
