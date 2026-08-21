package com.fabric.adp.adapters.out.jdbc;

import com.fabric.adp.application.PromptStore;
import com.fabric.adp.domain.PromptPack;
import com.fabric.adp.domain.PromptRoleTemplate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcPromptStore implements PromptStore {

  private static final String SELECT =
      """
      SELECT p.prompt_id, p.prompt_version, p.host, p.status, p.owner,
             t.llm_role, t.task_type, t."text" AS role_text
        FROM dataplane.prompt_packs p
        LEFT JOIN dataplane.prompt_role_templates t
          ON t.prompt_id = p.prompt_id AND t.prompt_version = p.prompt_version
      """;

  private final NamedParameterJdbcTemplate jdbc;

  public JdbcPromptStore(NamedParameterJdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  @Override
  public Optional<PromptPack> find(String promptId, String promptVersion) {
    return pack(
        jdbc.query(
            SELECT
                + """
                 WHERE p.prompt_id = :id AND p.prompt_version = :version
                 ORDER BY t.llm_role
                """,
            new MapSqlParameterSource().addValue("id", promptId).addValue("version", promptVersion),
            (rs, n) -> map(rs)));
  }

  @Override
  public Optional<PromptPack> findPublished(String promptId) {
    return pack(
        jdbc.query(
            """
            SELECT p.prompt_id, p.prompt_version, p.host, p.status, p.owner,
                   t.llm_role, t.task_type, t."text" AS role_text
              FROM (
                SELECT prompt_id, prompt_version, host, status, owner
                  FROM dataplane.prompt_packs
                 WHERE prompt_id = :id AND status = 'published'
                 ORDER BY string_to_array(prompt_version, '.')::int[] DESC
                 LIMIT 1
              ) p
              LEFT JOIN dataplane.prompt_role_templates t
                ON t.prompt_id = p.prompt_id AND t.prompt_version = p.prompt_version
             ORDER BY t.llm_role
            """,
            new MapSqlParameterSource("id", promptId),
            (rs, n) -> map(rs)));
  }

  @Override
  public List<PromptPack> listPublished() {
    return group(
        jdbc.query(
            """
            SELECT p.prompt_id, p.prompt_version, p.host, p.status, p.owner,
                   t.llm_role, t.task_type, t."text" AS role_text
              FROM (
                SELECT DISTINCT ON (prompt_id)
                       prompt_id, prompt_version, host, status, owner
                  FROM dataplane.prompt_packs
                 WHERE status = 'published'
                 ORDER BY prompt_id, string_to_array(prompt_version, '.')::int[] DESC
              ) p
              LEFT JOIN dataplane.prompt_role_templates t
                ON t.prompt_id = p.prompt_id AND t.prompt_version = p.prompt_version
             ORDER BY p.prompt_id, t.llm_role
            """,
            new MapSqlParameterSource(),
            (rs, n) -> map(rs)));
  }

  @Override
  public List<PromptPack> listAll() {
    return group(
        jdbc.query(
            SELECT
                + """
                 ORDER BY p.prompt_id, string_to_array(p.prompt_version, '.')::int[] DESC, t.llm_role
                """,
            new MapSqlParameterSource(),
            (rs, n) -> map(rs)));
  }

  @Override
  public List<PromptPack> listVersions(String promptId) {
    return group(
        jdbc.query(
            SELECT
                + """
                 WHERE p.prompt_id = :id
                 ORDER BY string_to_array(p.prompt_version, '.')::int[] DESC, t.llm_role
                """,
            new MapSqlParameterSource("id", promptId),
            (rs, n) -> map(rs)));
  }

  private static List<PromptPack> group(List<Row> rows) {
    Map<String, List<Row>> grouped = new LinkedHashMap<>();
    for (Row row : rows) {
      grouped
          .computeIfAbsent(row.promptId() + "@" + row.promptVersion(), ignored -> new ArrayList<>())
          .add(row);
    }
    List<PromptPack> packs = new ArrayList<>();
    for (List<Row> group : grouped.values()) {
      pack(group).ifPresent(packs::add);
    }
    return packs;
  }

  private static Optional<PromptPack> pack(List<Row> rows) {
    if (rows.isEmpty()) {
      return Optional.empty();
    }
    Row first = rows.getFirst();
    Map<String, PromptRoleTemplate> roles = new LinkedHashMap<>();
    for (Row row : rows) {
      if (row.llmRole() != null) {
        roles.put(
            row.llmRole(), new PromptRoleTemplate(row.llmRole(), row.taskType(), row.roleText()));
      }
    }
    return Optional.of(
        new PromptPack(
            first.promptId(),
            first.promptVersion(),
            first.host(),
            first.status(),
            first.owner(),
            new ArrayList<>(roles.values())));
  }

  private static Row map(java.sql.ResultSet rs) throws java.sql.SQLException {
    return new Row(
        rs.getString("prompt_id"),
        rs.getString("prompt_version"),
        rs.getString("host"),
        rs.getString("status"),
        rs.getString("owner"),
        rs.getString("llm_role"),
        rs.getString("task_type"),
        rs.getString("role_text"));
  }

  private record Row(
      String promptId,
      String promptVersion,
      String host,
      String status,
      String owner,
      String llmRole,
      String taskType,
      String roleText) {}
}
