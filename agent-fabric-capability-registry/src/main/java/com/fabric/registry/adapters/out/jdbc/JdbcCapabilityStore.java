package com.fabric.registry.adapters.out.jdbc;

import com.fabric.registry.application.CapabilityStore;
import com.fabric.registry.domain.CapabilityVersion;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcCapabilityStore implements CapabilityStore {

  private final NamedParameterJdbcTemplate jdbc;

  public JdbcCapabilityStore(NamedParameterJdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  @Override
  public Optional<CapabilityVersion> find(String id, String version) {
    var params = new MapSqlParameterSource().addValue("id", id).addValue("version", version);
    var rows =
        jdbc.query(
            """
            SELECT id, version, kind, description, input_schema::text, output_schema::text,
                   invoke::text, snippet, owner, status
              FROM registry.capabilities
             WHERE id = :id AND version = :version
            """,
            params,
            (rs, rowNum) -> mapRow(rs));
    return rows.stream().findFirst();
  }

  @Override
  public List<CapabilityVersion> listPublished(String query) {
    String needle = query == null ? "" : query.trim();
    var params = new MapSqlParameterSource().addValue("q", needle);
    return jdbc.query(
        """
        SELECT id, version, kind, description, input_schema::text, output_schema::text,
               invoke::text, snippet, owner, status
          FROM (
            SELECT DISTINCT ON (id)
                   id, version, kind, description, input_schema, output_schema,
                   invoke, snippet, owner, status
              FROM registry.capabilities
             WHERE status = 'published'
             ORDER BY id, string_to_array(version, '.')::int[] DESC
          ) latest
         WHERE :q = ''
            OR id ILIKE '%' || :q || '%'
            OR coalesce(description, '') ILIKE '%' || :q || '%'
         ORDER BY id
        """,
        params,
        (rs, rowNum) -> mapRow(rs));
  }

  @Override
  public List<CapabilityVersion> listAll(String query) {
    String needle = query == null ? "" : query.trim();
    var params = new MapSqlParameterSource().addValue("q", needle);
    return jdbc.query(
        """
        SELECT id, version, kind, description, input_schema::text, output_schema::text,
               invoke::text, snippet, owner, status
          FROM registry.capabilities
         WHERE :q = ''
            OR id ILIKE '%' || :q || '%'
            OR coalesce(description, '') ILIKE '%' || :q || '%'
         ORDER BY id, string_to_array(version, '.')::int[] DESC
        """,
        params,
        (rs, rowNum) -> mapRow(rs));
  }

  @Override
  public List<CapabilityVersion> listVersions(String id) {
    var params = new MapSqlParameterSource().addValue("id", id);
    return jdbc.query(
        """
        SELECT id, version, kind, description, input_schema::text, output_schema::text,
               invoke::text, snippet, owner, status
          FROM registry.capabilities
         WHERE id = :id
         ORDER BY string_to_array(version, '.')::int[] DESC
        """,
        params,
        (rs, rowNum) -> mapRow(rs));
  }

  @Override
  public void upsert(CapabilityVersion capability) {
    var params =
        new MapSqlParameterSource()
            .addValue("id", capability.id())
            .addValue("version", capability.version())
            .addValue("kind", capability.kind())
            .addValue("description", capability.description())
            .addValue("inputSchema", capability.inputSchemaJson())
            .addValue("outputSchema", capability.outputSchemaJson())
            .addValue("invoke", capability.invokeJson())
            .addValue("snippet", capability.snippet())
            .addValue("owner", capability.owner())
            .addValue("status", capability.status());
    jdbc.update(
        """
        INSERT INTO registry.capabilities (
          id, version, kind, description, input_schema, output_schema, invoke, snippet, owner, status
        ) VALUES (
          :id, :version, :kind, :description,
          CAST(:inputSchema AS jsonb), CAST(:outputSchema AS jsonb), CAST(:invoke AS jsonb),
          :snippet, :owner, :status
        )
        ON CONFLICT (id, version) DO UPDATE SET
          kind = EXCLUDED.kind,
          description = EXCLUDED.description,
          input_schema = EXCLUDED.input_schema,
          output_schema = EXCLUDED.output_schema,
          invoke = EXCLUDED.invoke,
          snippet = EXCLUDED.snippet,
          owner = EXCLUDED.owner,
          status = EXCLUDED.status
        """,
        params);
  }

  private static CapabilityVersion mapRow(ResultSet rs) throws SQLException {
    return new CapabilityVersion(
        rs.getString("id"),
        rs.getString("version"),
        rs.getString("kind"),
        rs.getString("description"),
        rs.getString("input_schema"),
        rs.getString("output_schema"),
        rs.getString("invoke"),
        rs.getString("snippet"),
        rs.getString("owner"),
        rs.getString("status"));
  }
}
