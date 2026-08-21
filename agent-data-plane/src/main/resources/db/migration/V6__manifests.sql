CREATE TABLE dataplane.manifests (
  manifest_id TEXT NOT NULL,
  manifest_version TEXT NOT NULL,
  description TEXT,
  tools JSONB NOT NULL DEFAULT '[]'::jsonb,
  PRIMARY KEY (manifest_id, manifest_version)
);

INSERT INTO dataplane.manifests (manifest_id, manifest_version, description, tools) VALUES
(
  'fee_explain_v1',
  '2026.08.1',
  'Look up why an account fee was charged',
  $$[
    {
      "name": "account_fee_lookup",
      "description": "Look up fee amount and reason for an account",
      "schema": {
        "type": "object",
        "required": ["account_id"],
        "properties": {
          "account_id": { "type": "string" }
        }
      },
      "pdp_action": "account_fee_lookup",
      "risk_tier": "low"
    }
  ]$$::jsonb
),
(
  'accounts-readonly-v2',
  '2026.08.1',
  'Read-only account and transaction lookup',
  $$[
    {
      "name": "list_accounts",
      "description": "List accounts for the entitled user",
      "schema": {
        "type": "object",
        "properties": {
          "customer_id": { "type": "string" }
        }
      },
      "pdp_action": "list_accounts",
      "risk_tier": "low"
    },
    {
      "name": "list_transactions",
      "description": "List transactions for an account",
      "schema": {
        "type": "object",
        "required": ["account_id"],
        "properties": {
          "account_id": { "type": "string" }
        }
      },
      "pdp_action": "list_transactions",
      "risk_tier": "low"
    }
  ]$$::jsonb
),
(
  'payments-readwrite-v3',
  '2026.07.1',
  'Lookup, validate, and initiate outbound wires',
  $$[
    {
      "name": "lookup_beneficiary",
      "description": "Resolve payee name and invoice to beneficiary id",
      "schema": {
        "type": "object",
        "required": ["payee_name", "invoice_ref"],
        "properties": {
          "payee_name": { "type": "string" },
          "invoice_ref": { "type": "string" }
        }
      },
      "pdp_action": "lookup_beneficiary",
      "risk_tier": "low"
    },
    {
      "name": "validate_payment",
      "description": "Pre-auth: limits, sanctions, cut-off for a payment",
      "schema": {
        "type": "object",
        "required": ["beneficiary_id", "amount", "source_account", "reference"],
        "properties": {
          "beneficiary_id": { "type": "string" },
          "amount": { "type": "number" },
          "source_account": { "type": "string" },
          "reference": { "type": "string" }
        }
      },
      "pdp_action": "validate_payment",
      "risk_tier": "medium"
    },
    {
      "name": "initiate_wire",
      "description": "Initiate wire transfer on payment hub",
      "schema": {
        "type": "object",
        "required": ["beneficiary_id", "amount", "source_account", "reference"],
        "properties": {
          "beneficiary_id": { "type": "string" },
          "amount": { "type": "number" },
          "source_account": { "type": "string" },
          "reference": { "type": "string" }
        }
      },
      "pdp_action": "initiate_wire",
      "risk_tier": "high",
      "idempotency_required": true
    }
  ]$$::jsonb
),
(
  'handoff-v1',
  '2026.08.1',
  'Hand off the conversation to a human agent',
  $$[
    {
      "name": "escalate_to_human",
      "description": "Open a human-agent handoff with conversation context",
      "schema": {
        "type": "object",
        "required": ["reason"],
        "properties": {
          "reason": { "type": "string" }
        }
      },
      "pdp_action": "escalate_to_human",
      "risk_tier": "medium"
    }
  ]$$::jsonb
);

ALTER TABLE dataplane.routes ALTER COLUMN tool_manifest DROP NOT NULL;

UPDATE dataplane.routes
   SET tool_manifest = NULL,
       tool_manifest_version = NULL
 WHERE tool_manifest = 'none';

UPDATE dataplane.routes
   SET tool_manifest_version = '2026.07.1'
 WHERE route_id = 'agent-payments-v2'
   AND route_table_version = '2026.08.1'
   AND tool_manifest = 'payments-readwrite-v3';

ALTER TABLE dataplane.routes
  ADD CONSTRAINT routes_tool_manifest_fk
  FOREIGN KEY (tool_manifest, tool_manifest_version)
  REFERENCES dataplane.manifests (manifest_id, manifest_version);
