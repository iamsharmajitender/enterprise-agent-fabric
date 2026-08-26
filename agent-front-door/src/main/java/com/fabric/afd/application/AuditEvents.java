package com.fabric.afd.application;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

public final class AuditEvents {
  private AuditEvents() {}

  public static Map<String, Object> freezeWritten(
      String correlationId,
      String sessionId,
      String routeId,
      String routeVersion,
      String ingress) {
    return freezeWritten(correlationId, sessionId, routeId, routeVersion, ingress, null);
  }

  public static Map<String, Object> freezeWritten(
      String correlationId,
      String sessionId,
      String routeId,
      String routeVersion,
      String ingress,
      String parentCorrelationId) {
    Map<String, Object> payload = new LinkedHashMap<>();
    payload.put("route_id", routeId);
    payload.put("route_version", routeVersion);
    payload.put("ingress", ingress);
    payload.put("freeze_key", sessionId);
    if (parentCorrelationId != null && !parentCorrelationId.isBlank()) {
      payload.put("parent_correlation_id", parentCorrelationId);
    }
    return envelope("freeze.written", "afd", correlationId, sessionId, null, payload);
  }

  public static Map<String, Object> envelope(
      String eventType,
      String producer,
      String correlationId,
      String sessionId,
      String decisionId,
      Map<String, Object> payload) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("event_id", UUID.randomUUID().toString());
    body.put("event_type", eventType);
    body.put("occurred_at", Instant.now().toString());
    body.put("producer", producer);
    body.put("correlation_id", correlationId);
    body.put("session_id", sessionId);
    body.put("decision_id", decisionId);
    body.put("payload", payload);
    return body;
  }
}
