-- overdraft_fee_qa — remove catalogue rows for this route pack.

\c adp
DELETE FROM dataplane.intent_rules WHERE route_id = 'overdraft_fee_qa';
DELETE FROM dataplane.retrieval WHERE route_id = 'overdraft_fee_qa';
DELETE FROM dataplane.routes WHERE route_id = 'overdraft_fee_qa';
DELETE FROM dataplane.prompt_packs WHERE prompt_id = 'overdraft_fee_qa';
DELETE FROM dataplane.corpora WHERE corpus_id IN ('fee-schedule', 'product-disclosure');
