ALTER TABLE dataplane.routes
  ADD COLUMN pattern SMALLINT NOT NULL DEFAULT 0;

ALTER TABLE dataplane.routes
  ADD CONSTRAINT routes_pattern_chk CHECK (pattern BETWEEN 0 AND 3);

-- Pattern 0 is the default (talk, Q&A, read-and-format, one-shot jobs).
-- Pattern 1: open tool loop. Pattern 2: write path or fixed-stage workflow.
UPDATE dataplane.routes SET pattern = 1
 WHERE route_id IN ('fee_explain', 'contract_investigation', 'agent-research-v0');

UPDATE dataplane.routes SET pattern = 2
 WHERE route_id IN ('agent-payments-v2', 'msa_risk_review', 'kyc_onboarding');
