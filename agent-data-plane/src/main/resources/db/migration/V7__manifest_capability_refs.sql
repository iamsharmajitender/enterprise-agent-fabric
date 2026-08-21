UPDATE dataplane.manifests
   SET tools = $$[
     {
       "name": "account_fee_lookup",
       "capability_id": "account_fee_lookup",
       "capability_version": "1.0.0",
       "pdp_action": "account_fee_lookup",
       "risk_tier": "low"
     }
   ]$$::jsonb
 WHERE manifest_id = 'fee_explain_v1' AND manifest_version = '2026.08.1';

UPDATE dataplane.manifests
   SET tools = $$[
     {
       "name": "list_accounts",
       "capability_id": "list_accounts",
       "capability_version": "1.0.0",
       "pdp_action": "list_accounts",
       "risk_tier": "low"
     },
     {
       "name": "list_transactions",
       "capability_id": "list_transactions",
       "capability_version": "1.0.0",
       "pdp_action": "list_transactions",
       "risk_tier": "low"
     }
   ]$$::jsonb
 WHERE manifest_id = 'accounts-readonly-v2' AND manifest_version = '2026.08.1';

UPDATE dataplane.manifests
   SET tools = $$[
     {
       "name": "lookup_beneficiary",
       "capability_id": "lookup_beneficiary",
       "capability_version": "1.0.0",
       "pdp_action": "lookup_beneficiary",
       "risk_tier": "low"
     },
     {
       "name": "validate_payment",
       "capability_id": "validate_payment",
       "capability_version": "1.0.0",
       "pdp_action": "validate_payment",
       "risk_tier": "medium"
     },
     {
       "name": "initiate_wire",
       "capability_id": "initiate_wire",
       "capability_version": "1.0.0",
       "pdp_action": "initiate_wire",
       "risk_tier": "high"
     }
   ]$$::jsonb
 WHERE manifest_id = 'payments-readwrite-v3' AND manifest_version = '2026.07.1';

UPDATE dataplane.manifests
   SET tools = $$[
     {
       "name": "escalate_to_human",
       "capability_id": "escalate_to_human",
       "capability_version": "1.0.0",
       "pdp_action": "escalate_to_human",
       "risk_tier": "medium"
     }
   ]$$::jsonb
 WHERE manifest_id = 'handoff-v1' AND manifest_version = '2026.08.1';

INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools) VALUES
(
  'fraud_investigate_v2',
  '2026.08.1',
  'Fraud investigate: domain tools plus Legal start',
  $$[
    {
      "name": "search_transactions",
      "capability_id": "search_transactions",
      "capability_version": "1.4.0",
      "pdp_action": "search_transactions",
      "risk_tier": "low"
    },
    {
      "name": "ocr_extract",
      "capability_id": "ocr_extract",
      "capability_version": "1.2.0",
      "pdp_action": "ocr_extract",
      "risk_tier": "low"
    },
    {
      "name": "start_contract_review",
      "capability_id": "start_contract_review",
      "capability_version": "1.0.0",
      "pdp_action": "start_contract_review",
      "risk_tier": "high"
    }
  ]$$::jsonb
);
