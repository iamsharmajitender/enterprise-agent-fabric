-- duplicate_charge_review — fixed Pattern 2 stage list (2 LLM + 2 HTTP tools).

\c adp
INSERT INTO dataplane.workflows (
  workflow_id, workflow_version, description, stages, status
) VALUES
(
  'duplicate_charge_review', '2026.08.1',
  'Pattern 2: classify order id, lookup order, duplicate check (customer_id from lookup slot), synthesis reply',
  $$[
    {"id":"intake","tool":"duplicate_charge_intake","llm_role":"classify"},
    {"id":"order_lookup","tool":"lookup_order_by_order_id","llm_role":"none"},
    {"id":"dup_check","tool":"investigate_duplicate_charge","llm_role":"none"},
    {"id":"respond","tool":"duplicate_charge_respond","llm_role":"synthesis"}
  ]$$::jsonb,
  'published'
)
ON CONFLICT (workflow_id, workflow_version) DO UPDATE SET
  description = EXCLUDED.description,
  stages = EXCLUDED.stages,
  status = EXCLUDED.status;
