package com.fabric.adp.application;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public final class AuditEvents {
  private AuditEvents() {}

  public static Map<String, Object> decide(
      String decisionId,
      String sessionId,
      String outcome,
      String routeId,
      String routeVersion,
      List<String> candidates,
      String routerLayer,
      String claimsHash,
      String utteranceHash,
      String channel,
      String ingress) {
    Map<String, Object> payload = new LinkedHashMap<>();
    payload.put("outcome", outcome);
    payload.put("route_id", routeId);
    payload.put("route_version", routeVersion);
    payload.put("candidates", candidates == null ? List.of() : candidates);
    payload.put("router_layer", routerLayer);
    payload.put("claims_hash", claimsHash);
    payload.put("utterance_hash", utteranceHash);
    payload.put("channel", channel);
    payload.put("ingress", ingress);
    String type =
        switch (outcome == null ? "" : outcome) {
          case "route" -> "decide.completed";
          case "clarify" -> "decide.clarify";
          default -> "decide.abstain";
        };
    return envelope(type, "adp", null, sessionId, decisionId, payload);
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

  public static String sha256Hex(String raw) {
    if (raw == null) {
      raw = "";
    }
    try {
      byte[] dig =
          MessageDigest.getInstance("SHA-256").digest(raw.getBytes(StandardCharsets.UTF_8));
      return "sha256:" + HexFormat.of().formatHex(dig);
    } catch (Exception ex) {
      return "sha256:unavailable";
    }
  }
}
