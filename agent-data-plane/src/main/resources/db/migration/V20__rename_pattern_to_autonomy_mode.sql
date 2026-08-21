-- V17 shipped as `pattern`. Catalogue contract is `autonomy_mode`.
UPDATE dataplane.routes SET pattern = 0 WHERE route_id = 'fee_explain';

ALTER TABLE dataplane.routes DROP CONSTRAINT routes_pattern_chk;
ALTER TABLE dataplane.routes RENAME COLUMN pattern TO autonomy_mode;
ALTER TABLE dataplane.routes
  ADD CONSTRAINT routes_autonomy_mode_chk CHECK (autonomy_mode BETWEEN 0 AND 3);
