package com.fabric.aadp.adapters.out.jdbc;

import com.fabric.aadp.application.AuditEventStore;
import com.fabric.aadp.domain.AuditEvent;
import com.fabric.aadp.domain.CompletedWorkflow;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class JdbcAuditEventStore implements AuditEventStore {

  private static final TypeReference<Map<String, Object>> MAP = new TypeReference<>() {};

  private final NamedParameterJdbcTemplate jdbc;
  private final ObjectMapper mapper;

  public JdbcAuditEventStore(NamedParameterJdbcTemplate jdbc, ObjectMapper mapper) {
    this.jdbc = jdbc;
    this.mapper = mapper;
  }

  @Override
  public boolean insertIdempotent(AuditEvent event) {
    String json;
    try {
      json = mapper.writeValueAsString(event.payload());
    } catch (JsonProcessingException e) {
      throw new IllegalArgumentException("payload not serializable", e);
    }
    MapSqlParameterSource params =
        new MapSqlParameterSource()
            .addValue("event_id", event.eventId())
            .addValue("event_type", event.eventType())
            .addValue("occurred_at", Timestamp.from(event.occurredAt()))
            .addValue("producer", event.producer())
            .addValue("correlation_id", event.correlationId())
            .addValue("session_id", event.sessionId())
            .addValue("decision_id", event.decisionId())
            .addValue("payload", json);
    try {
      int rows =
          jdbc.update(
              """
              INSERT INTO audit.events (
                event_id, event_type, occurred_at, producer,
                correlation_id, session_id, decision_id, payload)
              VALUES (
                :event_id, :event_type, :occurred_at, :producer,
                :correlation_id, :session_id, :decision_id, CAST(:payload AS jsonb))
              """,
              params);
      return rows > 0;
    } catch (DuplicateKeyException dup) {
      return false;
    }
  }

  @Override
  public Optional<AuditEvent> findById(UUID eventId) {
    List<AuditEvent> rows =
        jdbc.query(
            """
            SELECT event_id, event_type, occurred_at, producer,
                   correlation_id, session_id, decision_id, payload::text AS payload
            FROM audit.events WHERE event_id = :event_id
            """,
            new MapSqlParameterSource("event_id", eventId),
            (rs, i) -> mapRow(rs));
    return rows.stream().findFirst();
  }

  @Override
  public List<AuditEvent> findByCorrelationId(String correlationId) {
    return jdbc.query(
        """
        SELECT event_id, event_type, occurred_at, producer,
               correlation_id, session_id, decision_id, payload::text AS payload
        FROM audit.events
        WHERE correlation_id = :correlation_id
        ORDER BY occurred_at ASC, received_at ASC
        """,
        new MapSqlParameterSource("correlation_id", correlationId),
        (rs, i) -> mapRow(rs));
  }

  @Override
  public List<AuditEvent> findBySessionId(String sessionId) {
    return jdbc.query(
        """
        SELECT event_id, event_type, occurred_at, producer,
               correlation_id, session_id, decision_id, payload::text AS payload
        FROM audit.events
        WHERE session_id = :session_id
        ORDER BY occurred_at ASC, received_at ASC
        """,
        new MapSqlParameterSource("session_id", sessionId),
        (rs, i) -> mapRow(rs));
  }

  @Override
  public List<CompletedWorkflow> findCompletedWorkflows(int limit, int offset) {
    return jdbc.query(
        """
        WITH terminals AS (
          SELECT DISTINCT ON (correlation_id)
            correlation_id,
            session_id,
            decision_id,
            occurred_at AS completed_at,
            payload
          FROM audit.events
          WHERE event_type = 'run.terminal'
            AND correlation_id IS NOT NULL
            AND payload->>'status' = 'completed'
          ORDER BY correlation_id, occurred_at DESC, received_at DESC
        )
        SELECT
          t.correlation_id,
          t.session_id,
          t.decision_id,
          t.payload->>'route_id' AS route_id,
          t.payload->>'route_version' AS route_version,
          t.payload->>'status' AS status,
          (SELECT MIN(e.occurred_at) FROM audit.events e
             WHERE e.correlation_id = t.correlation_id) AS started_at,
          t.completed_at
        FROM terminals t
        ORDER BY t.completed_at DESC
        LIMIT :limit OFFSET :offset
        """,
        new MapSqlParameterSource().addValue("limit", limit).addValue("offset", offset),
        (rs, i) -> mapWorkflow(rs));
  }

  @Override
  public long countCompletedWorkflows() {
    Long count =
        jdbc.queryForObject(
            """
            SELECT COUNT(DISTINCT correlation_id)
            FROM audit.events
            WHERE event_type = 'run.terminal'
              AND correlation_id IS NOT NULL
              AND payload->>'status' = 'completed'
            """,
            new MapSqlParameterSource(),
            Long.class);
    return count == null ? 0L : count;
  }

  private static CompletedWorkflow mapWorkflow(ResultSet rs) throws SQLException {
    Timestamp started = rs.getTimestamp("started_at");
    Timestamp completed = rs.getTimestamp("completed_at");
    return new CompletedWorkflow(
        rs.getString("correlation_id"),
        rs.getString("session_id"),
        rs.getString("decision_id"),
        rs.getString("route_id"),
        rs.getString("route_version"),
        rs.getString("status"),
        started == null ? Instant.EPOCH : started.toInstant(),
        completed == null ? Instant.EPOCH : completed.toInstant());
  }

  private AuditEvent mapRow(ResultSet rs) throws SQLException {
    Map<String, Object> payload;
    try {
      payload = mapper.readValue(rs.getString("payload"), MAP);
    } catch (JsonProcessingException e) {
      payload = Map.of();
    }
    Timestamp occurred = rs.getTimestamp("occurred_at");
    Instant instant = occurred == null ? Instant.EPOCH : occurred.toInstant();
    return new AuditEvent(
        (UUID) rs.getObject("event_id"),
        rs.getString("event_type"),
        instant,
        rs.getString("producer"),
        rs.getString("correlation_id"),
        rs.getString("session_id"),
        rs.getString("decision_id"),
        payload);
  }
}
