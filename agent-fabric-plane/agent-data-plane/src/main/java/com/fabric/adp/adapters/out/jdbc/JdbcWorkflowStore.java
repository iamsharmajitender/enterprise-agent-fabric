package com.fabric.adp.adapters.out.jdbc;

import com.fabric.adp.application.WorkflowStore;
import com.fabric.adp.domain.Workflow;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcWorkflowStore implements WorkflowStore {

  private static final String SELECT =
      """
      SELECT workflow_id, workflow_version, description, stages::text, status
        FROM dataplane.workflows
      """;

  private final NamedParameterJdbcTemplate jdbc;
  private final WorkflowMapper workflows;

  public JdbcWorkflowStore(NamedParameterJdbcTemplate jdbc, ObjectMapper mapper) {
    this.jdbc = jdbc;
    this.workflows = new WorkflowMapper(mapper);
  }

  @Override
  public Optional<Workflow> find(String workflowId, String workflowVersion) {
    return jdbc
        .query(
            SELECT
                + """
                 WHERE workflow_id = :id AND workflow_version = :version
                """,
            new MapSqlParameterSource()
                .addValue("id", workflowId)
                .addValue("version", workflowVersion),
            (rs, n) -> mapRow(rs))
        .stream()
        .findFirst();
  }

  @Override
  public List<Workflow> listLatest() {
    return jdbc.query(
        """
        SELECT workflow_id, workflow_version, description, stages::text, status
          FROM (
            SELECT DISTINCT ON (workflow_id)
                   workflow_id, workflow_version, description, stages, status
              FROM dataplane.workflows
             ORDER BY workflow_id, string_to_array(workflow_version, '.')::int[] DESC
          ) latest
         ORDER BY workflow_id
        """,
        (rs, n) -> mapRow(rs));
  }

  @Override
  public List<Workflow> listAll() {
    return jdbc.query(
        SELECT
            + """
             ORDER BY workflow_id, string_to_array(workflow_version, '.')::int[] DESC
            """,
        (rs, n) -> mapRow(rs));
  }

  @Override
  public List<Workflow> listVersions(String workflowId) {
    return jdbc.query(
        SELECT
            + """
             WHERE workflow_id = :id
             ORDER BY string_to_array(workflow_version, '.')::int[] DESC
            """,
        new MapSqlParameterSource("id", workflowId),
        (rs, n) -> mapRow(rs));
  }

  private Workflow mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
    return workflows.parse(
        rs.getString("workflow_id"),
        rs.getString("workflow_version"),
        rs.getString("description"),
        rs.getString("stages"),
        rs.getString("status"));
  }
}
