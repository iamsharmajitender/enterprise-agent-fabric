package com.fabric.adp.adapters.out.jdbc;

import com.fabric.adp.application.IntentRuleStore;
import com.fabric.adp.domain.IntentRule;
import java.util.List;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcIntentRuleStore implements IntentRuleStore {

  private static final String SELECT =
      """
      SELECT rule_id, match_kind, match_value, route_id, sort_order
        FROM dataplane.intent_rules
       ORDER BY sort_order, rule_id
      """;

  private final NamedParameterJdbcTemplate jdbc;

  public JdbcIntentRuleStore(NamedParameterJdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  @Override
  public List<IntentRule> list() {
    return jdbc.query(SELECT, (rs, n) -> mapRow(rs));
  }

  private static IntentRule mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
    return new IntentRule(
        rs.getString("rule_id"),
        rs.getString("match_kind"),
        rs.getString("match_value"),
        rs.getString("route_id"),
        rs.getInt("sort_order"));
  }
}
