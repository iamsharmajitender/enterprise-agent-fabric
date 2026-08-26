package com.fabric.registry.application;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

public final class AuditEvents {
  private AuditEvents() {}

  public static Map<String, Object> capabilityPublished(String id, String version, String bodyJson) {
    Map<String, Object> payload = new LinkedHashMap<>();
    payload.put("capability_id", id);
    payload.put("capability_version", version);
    payload.put("content_digest", sha256(bodyJson));
    return envelope("capability.published", payload);
  }

  public static Map<String, Object> manifestPublished(String id, String version, String toolsJson) {
    Map<String, Object> payload = new LinkedHashMap<>();
    payload.put("manifest_id", id);
    payload.put("manifest_version", version);
    payload.put("content_digest", sha256(toolsJson));
    return envelope("manifest.published", payload);
  }

  private static Map<String, Object> envelope(String type, Map<String, Object> payload) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("event_id", UUID.randomUUID().toString());
    body.put("event_type", type);
    body.put("occurred_at", Instant.now().toString());
    body.put("producer", "acr");
    body.put("correlation_id", null);
    body.put("session_id", null);
    body.put("decision_id", null);
    body.put("payload", payload);
    return body;
  }

  private static String sha256(String raw) {
    try {
      byte[] dig =
          MessageDigest.getInstance("SHA-256")
              .digest((raw == null ? "" : raw).getBytes(StandardCharsets.UTF_8));
      return "sha256:" + HexFormat.of().formatHex(dig);
    } catch (Exception ex) {
      return "sha256:unavailable";
    }
  }
}
