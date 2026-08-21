package com.fabric.adp.adapters.out.jdbc;

import com.fabric.adp.application.CorpusStore;
import com.fabric.adp.domain.Corpus;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcCorpusStore implements CorpusStore {

  private static final String SELECT =
      """
      SELECT corpus_id, display_name, url, collection, auth, owner, status, region, updated_at
        FROM dataplane.corpora
      """;

  private final NamedParameterJdbcTemplate jdbc;

  public JdbcCorpusStore(NamedParameterJdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  @Override
  public Optional<Corpus> find(String corpusId) {
    return jdbc
        .query(
            SELECT + " WHERE corpus_id = :id",
            new MapSqlParameterSource("id", corpusId),
            (rs, n) -> mapRow(rs))
        .stream()
        .findFirst();
  }

  @Override
  public List<Corpus> listPublished() {
    return jdbc.query(
        SELECT + " WHERE status = 'published' ORDER BY corpus_id", (rs, n) -> mapRow(rs));
  }

  @Override
  public List<Corpus> listAll() {
    return jdbc.query(SELECT + " ORDER BY corpus_id", (rs, n) -> mapRow(rs));
  }

  private static Corpus mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
    OffsetDateTime updated = rs.getObject("updated_at", OffsetDateTime.class);
    return new Corpus(
        rs.getString("corpus_id"),
        rs.getString("display_name"),
        rs.getString("url"),
        rs.getString("collection"),
        rs.getString("auth"),
        rs.getString("owner"),
        rs.getString("status"),
        rs.getString("region"),
        updated == null ? null : updated.toInstant());
  }
}
