package com.fabric.afd.adapters.out.jdbc;

import com.fabric.afd.application.FreezeStore;
import com.fabric.afd.domain.FrozenRoute;
import java.time.Duration;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

public class JdbcFreezeStore implements FreezeStore {

  static final Duration TTL = Duration.ofMinutes(45);

  private final NamedParameterJdbcTemplate jdbc;

  public JdbcFreezeStore(NamedParameterJdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  @Override
  public void save(FrozenRoute freeze) {
    OffsetDateTime expires = OffsetDateTime.now(ZoneOffset.UTC).plus(TTL);
    var params =
        new MapSqlParameterSource()
            .addValue("session_id", freeze.sessionId())
            .addValue("idempotency_key", freeze.idempotencyKey())
            .addValue("route_id", freeze.routeId())
            .addValue("route_version", freeze.routeVersion())
            .addValue("activation_target", freeze.activationTarget())
            .addValue("agent_client_id", freeze.agentClientId())
            .addValue("correlation_id", freeze.correlationId())
            .addValue("expires_at", expires);
    jdbc.update(
        """
        INSERT INTO frontdoor.freeze (
            session_id, idempotency_key, route_id, route_version,
            activation_target, agent_client_id, correlation_id, expires_at, updated_at)
        VALUES (
            :session_id, :idempotency_key, :route_id, :route_version,
            :activation_target, :agent_client_id, :correlation_id, :expires_at, now())
        ON CONFLICT (session_id) DO UPDATE SET
            idempotency_key = EXCLUDED.idempotency_key,
            route_id = EXCLUDED.route_id,
            route_version = EXCLUDED.route_version,
            activation_target = EXCLUDED.activation_target,
            agent_client_id = EXCLUDED.agent_client_id,
            correlation_id = EXCLUDED.correlation_id,
            expires_at = EXCLUDED.expires_at,
            updated_at = now()
        """,
        params);
  }

  @Override
  public FrozenRoute get(String sessionId) {
    List<FrozenRoute> rows =
        jdbc.query(
            """
            SELECT session_id, idempotency_key, route_id, route_version,
                   activation_target, agent_client_id, correlation_id
              FROM frontdoor.freeze
             WHERE session_id = :session_id AND expires_at > now()
            """,
            new MapSqlParameterSource("session_id", sessionId),
            (rs, n) ->
                new FrozenRoute(
                    rs.getString("session_id"),
                    rs.getString("idempotency_key"),
                    rs.getString("route_id"),
                    rs.getString("route_version"),
                    rs.getString("activation_target"),
                    rs.getString("agent_client_id"),
                    rs.getString("correlation_id")));
    return rows.isEmpty() ? null : rows.getFirst();
  }

  @Override
  public void putOpaque(String sessionId, String opaqueId, String routeId) {
    var params =
        new MapSqlParameterSource()
            .addValue("session_id", sessionId)
            .addValue("opaque_id", opaqueId)
            .addValue("route_id", routeId)
            .addValue("expires_at", OffsetDateTime.now(ZoneOffset.UTC).plus(TTL));
    jdbc.update(
        """
        INSERT INTO frontdoor.opaque_ids (session_id, opaque_id, route_id, expires_at)
        VALUES (:session_id, :opaque_id, :route_id, :expires_at)
        ON CONFLICT (session_id, opaque_id) DO UPDATE SET
            route_id = EXCLUDED.route_id,
            expires_at = EXCLUDED.expires_at
        """,
        params);
  }

  @Override
  public String resolveOpaque(String sessionId, String opaqueId) {
    List<String> rows =
        jdbc.query(
            """
            SELECT route_id
              FROM frontdoor.opaque_ids
             WHERE session_id = :session_id AND opaque_id = :opaque_id AND expires_at > now()
            """,
            new MapSqlParameterSource()
                .addValue("session_id", sessionId)
                .addValue("opaque_id", opaqueId),
            (rs, n) -> rs.getString("route_id"));
    return rows.isEmpty() ? null : rows.getFirst();
  }
}
