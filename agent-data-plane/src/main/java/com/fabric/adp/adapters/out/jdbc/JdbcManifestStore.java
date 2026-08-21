package com.fabric.adp.adapters.out.jdbc;

import com.fabric.adp.application.ManifestStore;
import com.fabric.adp.domain.ToolManifest;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcManifestStore implements ManifestStore {

  private final NamedParameterJdbcTemplate jdbc;
  private final ManifestMapper manifests;

  public JdbcManifestStore(NamedParameterJdbcTemplate jdbc, ObjectMapper mapper) {
    this.jdbc = jdbc;
    this.manifests = new ManifestMapper(mapper);
  }

  @Override
  public Optional<ToolManifest> find(String manifestId, String manifestVersion) {
    return jdbc
        .query(
            """
            SELECT manifest_id, manifest_version, description, tools::text, status
              FROM dataplane.manifests
             WHERE manifest_id = :id AND manifest_version = :version
            """,
            new MapSqlParameterSource()
                .addValue("id", manifestId)
                .addValue("version", manifestVersion),
            (rs, n) ->
                manifests.parse(
                    rs.getString("manifest_id"),
                    rs.getString("manifest_version"),
                    rs.getString("description"),
                    rs.getString("tools"),
                    rs.getString("status")))
        .stream()
        .findFirst();
  }

  @Override
  public List<ToolManifest> listLatest() {
    return jdbc.query(
        """
        SELECT manifest_id, manifest_version, description, tools::text, status
          FROM (
            SELECT DISTINCT ON (manifest_id)
                   manifest_id, manifest_version, description, tools, status
              FROM dataplane.manifests
             ORDER BY manifest_id, string_to_array(manifest_version, '.')::int[] DESC
          ) latest
         ORDER BY manifest_id
        """,
        (rs, n) ->
            manifests.parse(
                rs.getString("manifest_id"),
                rs.getString("manifest_version"),
                rs.getString("description"),
                rs.getString("tools"),
                rs.getString("status")));
  }

  @Override
  public List<ToolManifest> listAll() {
    return jdbc.query(
        """
        SELECT manifest_id, manifest_version, description, tools::text, status
          FROM dataplane.manifests
         ORDER BY manifest_id, string_to_array(manifest_version, '.')::int[] DESC
        """,
        (rs, n) ->
            manifests.parse(
                rs.getString("manifest_id"),
                rs.getString("manifest_version"),
                rs.getString("description"),
                rs.getString("tools"),
                rs.getString("status")));
  }

  @Override
  public List<ToolManifest> listVersions(String manifestId) {
    return jdbc.query(
        """
        SELECT manifest_id, manifest_version, description, tools::text, status
          FROM dataplane.manifests
         WHERE manifest_id = :id
         ORDER BY string_to_array(manifest_version, '.')::int[] DESC
        """,
        new MapSqlParameterSource("id", manifestId),
        (rs, n) ->
            manifests.parse(
                rs.getString("manifest_id"),
                rs.getString("manifest_version"),
                rs.getString("description"),
                rs.getString("tools"),
                rs.getString("status")));
  }
}
