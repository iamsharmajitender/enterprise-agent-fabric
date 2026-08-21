package com.fabric.registry.adapters.out.jdbc;

import com.fabric.registry.application.ManifestStore;
import com.fabric.registry.domain.ManifestVersion;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcManifestStore implements ManifestStore {

  private final NamedParameterJdbcTemplate jdbc;

  public JdbcManifestStore(NamedParameterJdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  @Override
  public Optional<ManifestVersion> find(String manifestId, String manifestVersion) {
    var params =
        new MapSqlParameterSource()
            .addValue("manifestId", manifestId)
            .addValue("manifestVersion", manifestVersion);
    var rows =
        jdbc.query(
            """
            SELECT manifest_id, manifest_version, tools::text, status
              FROM registry.manifests
             WHERE manifest_id = :manifestId AND manifest_version = :manifestVersion
            """,
            params,
            (rs, rowNum) ->
                new ManifestVersion(
                    rs.getString("manifest_id"),
                    rs.getString("manifest_version"),
                    rs.getString("tools"),
                    rs.getString("status")));
    return rows.stream().findFirst();
  }

  @Override
  public void upsert(ManifestVersion manifest) {
    var params =
        new MapSqlParameterSource()
            .addValue("manifestId", manifest.manifestId())
            .addValue("manifestVersion", manifest.manifestVersion())
            .addValue("tools", manifest.toolsJson())
            .addValue("status", manifest.status());
    jdbc.update(
        """
        INSERT INTO registry.manifests (manifest_id, manifest_version, tools, status)
        VALUES (:manifestId, :manifestVersion, CAST(:tools AS jsonb), :status)
        ON CONFLICT (manifest_id, manifest_version) DO UPDATE SET
          tools = EXCLUDED.tools,
          status = EXCLUDED.status
        """,
        params);
  }
}
