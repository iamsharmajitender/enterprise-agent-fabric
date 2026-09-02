-- shopassist_case — remove catalogue rows for this route pack.

\c adp
DELETE FROM dataplane.intent_rules WHERE route_id = 'shopassist_case';
DELETE FROM dataplane.memory_profiles WHERE route_id = 'shopassist_case';
DELETE FROM dataplane.routes WHERE route_id = 'shopassist_case';
DELETE FROM dataplane.prompt_packs WHERE prompt_id = 'shopassist_case';
DELETE FROM dataplane.manifests WHERE manifest_id = 'shopassist_case';

\c acr
DELETE FROM registry.manifests WHERE manifest_id = 'shopassist_case';
DELETE FROM registry.capabilities WHERE id IN (
  'lookup_order_by_order_id',
  'investigate_duplicate_charge',
  'check_return_policy',
  'escalate_to_human'
);
