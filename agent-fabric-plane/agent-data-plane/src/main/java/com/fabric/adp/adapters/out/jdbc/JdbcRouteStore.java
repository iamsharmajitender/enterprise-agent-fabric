package com.fabric.adp.adapters.out.jdbc;

import com.fabric.adp.application.RouteStore;
import com.fabric.adp.domain.AutonomyPattern;
import com.fabric.adp.domain.MemoryProfile;
import com.fabric.adp.domain.ModelProfile;
import com.fabric.adp.domain.Retrieval;
import com.fabric.adp.domain.RouteRow;
import com.fabric.adp.domain.ToolManifest;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcRouteStore implements RouteStore {

  private static final TypeReference<List<String>> STRINGS = new TypeReference<>() {};

  private static final String ROUTE_SELECT =
      """
      SELECT r.route_id, r.route_version, r.active, r.status, r.intent_label, r.description,
             r.autonomy_mode, r.activation_target, r.agent_client_id, r.tool_manifest, r.tool_manifest_version,
             r.policy_profile, r.model_profile, r.workflow_id, r.prompt_id, r.output_schema_id,
             r.eval_suite_id, r.max_loop_steps, r.fallback, r.required_claims::text, r.channels::text,
             r.chat_visible, r.keywords::text,
             ret.mode AS retrieval_mode, ret.scope::text AS retrieval_scope,
             mem.conversation AS mem_conversation, mem.working AS mem_working,
             mem."loop" AS mem_loop, mem.long_term AS mem_long_term,
             mem.ttl_hours AS mem_ttl_hours, mem.isolation::text AS mem_isolation,
             m.description AS manifest_description, m.tools::text AS manifest_tools
        FROM dataplane.routes r
        LEFT JOIN dataplane.retrieval ret
          ON ret.route_id = r.route_id AND ret.route_version = r.route_version
        LEFT JOIN dataplane.memory_profiles mem
          ON mem.route_id = r.route_id AND mem.route_version = r.route_version
        LEFT JOIN dataplane.manifests m
          ON m.manifest_id = r.tool_manifest AND m.manifest_version = r.tool_manifest_version
      """;

  private final NamedParameterJdbcTemplate jdbc;
  private final ObjectMapper mapper;
  private final ManifestMapper manifests;

  public JdbcRouteStore(NamedParameterJdbcTemplate jdbc, ObjectMapper mapper) {
    this.jdbc = jdbc;
    this.mapper = mapper;
    this.manifests = new ManifestMapper(mapper);
  }

  @Override
  public List<RouteRow> activeRoutes() {
    return jdbc.query(
        ROUTE_SELECT
            + """
             WHERE r.active = TRUE
             ORDER BY r.route_id
            """,
        (rs, n) -> mapRow(rs));
  }

  @Override
  public List<RouteRow> allRoutes() {
    return jdbc.query(
        ROUTE_SELECT
            + """
             ORDER BY r.route_id, r.route_version DESC
            """,
        (rs, n) -> mapRow(rs));
  }

  @Override
  public Optional<RouteRow> activeRoute(String routeId) {
    return jdbc
        .query(
            ROUTE_SELECT
                + """
                 WHERE r.route_id = :id AND r.active = TRUE
                """,
            new MapSqlParameterSource("id", routeId),
            (rs, n) -> mapRow(rs))
        .stream()
        .findFirst();
  }

  @Override
  public Optional<RouteRow> route(String routeId, String routeVersion) {
    return jdbc
        .query(
            ROUTE_SELECT
                + """
                 WHERE r.route_id = :id AND r.route_version = :version
                """,
            new MapSqlParameterSource()
                .addValue("id", routeId)
                .addValue("version", routeVersion),
            (rs, n) -> mapRow(rs))
        .stream()
        .findFirst();
  }

  @Override
  public List<RouteRow> versions(String routeId) {
    return jdbc.query(
        ROUTE_SELECT
            + """
             WHERE r.route_id = :id
             ORDER BY r.route_version DESC
            """,
        new MapSqlParameterSource("id", routeId),
        (rs, n) -> mapRow(rs));
  }

  private RouteRow mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
    Retrieval retrieval =
        Retrieval.fromMode(rs.getString("retrieval_mode"), strings(rs.getString("retrieval_scope")));
    String conversation = rs.getString("mem_conversation");
    String working = rs.getString("mem_working");
    String loop = rs.getString("mem_loop");
    String longTerm = rs.getString("mem_long_term");
    Integer ttlHours = (Integer) rs.getObject("mem_ttl_hours");
    String isolationJson = rs.getString("mem_isolation");
    MemoryProfile memory =
        conversation == null && working == null && loop == null && longTerm == null && ttlHours == null
            ? null
            : new MemoryProfile(
                conversation, working, loop, longTerm, ttlHours, strings(isolationJson));
    ToolManifest manifest =
        manifests.parse(
            rs.getString("tool_manifest"),
            rs.getString("tool_manifest_version"),
            rs.getString("manifest_description"),
            rs.getString("manifest_tools"));
    return new RouteRow(
        rs.getString("route_id"),
        rs.getString("route_version"),
        rs.getBoolean("active"),
        rs.getString("intent_label"),
        rs.getString("description"),
        rs.getString("activation_target"),
        rs.getString("agent_client_id"),
        manifest,
        rs.getString("policy_profile"),
        ModelProfile.fromId(rs.getString("model_profile")),
        retrieval,
        memory,
        rs.getString("workflow_id"),
        rs.getString("prompt_id"),
        rs.getString("output_schema_id"),
        rs.getString("eval_suite_id"),
        (Integer) rs.getObject("max_loop_steps"),
        rs.getString("fallback"),
        strings(rs.getString("required_claims")),
        strings(rs.getString("channels")),
        rs.getBoolean("chat_visible"),
        strings(rs.getString("keywords")),
        AutonomyPattern.fromCode(rs.getInt("autonomy_mode")),
        rs.getString("status"));
  }

  private List<String> strings(String json) {
    if (json == null || json.isBlank()) {
      return List.of();
    }
    try {
      return mapper.readValue(json, STRINGS);
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }
}
