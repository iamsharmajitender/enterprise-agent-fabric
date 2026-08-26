package com.fabric.aadp.application;

import com.fabric.aadp.domain.AuditEvent;
import com.fabric.aadp.domain.AuditValidationException;
import com.fabric.aadp.domain.CompletedWorkflow;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

public class AuditEventService {

  private static final Set<String> PRODUCERS = Set.of("afd", "adp", "ar", "acr");
  private static final Set<String> DENY_PAYLOAD_KEYS =
      Set.of("utterance", "message", "claims", "authorization", "authorization_header", "prompt", "completion");

  private final AuditEventStore store;

  public AuditEventService(AuditEventStore store) {
    this.store = store;
  }

  public AuditEvent ingest(Map<String, Object> body) {
    AuditEvent event = parse(body);
    store.insertIdempotent(event);
    return event;
  }

  public List<AuditEvent> chain(String correlationId) {
    if (correlationId == null || correlationId.isBlank()) {
      throw new AuditValidationException("correlation_id is required");
    }
    return store.findByCorrelationId(correlationId.trim());
  }

  public List<AuditEvent> session(String sessionId) {
    if (sessionId == null || sessionId.isBlank()) {
      throw new AuditValidationException("session_id is required");
    }
    return store.findBySessionId(sessionId.trim());
  }

  public record WorkflowPage(List<CompletedWorkflow> items, long total, int limit, int offset) {}

  /** {@code status} is {@code completed} (default) or {@code in_progress}. */
  public WorkflowPage workflows(String status, int limit, int offset) {
    int safeLimit = Math.min(Math.max(limit, 1), 100);
    int safeOffset = Math.max(offset, 0);
    String bucket = status == null ? "completed" : status.trim().toLowerCase(Locale.ROOT);
    if ("in_progress".equals(bucket) || "in-progress".equals(bucket)) {
      return new WorkflowPage(
          store.findInProgressWorkflows(safeLimit, safeOffset),
          store.countInProgressWorkflows(),
          safeLimit,
          safeOffset);
    }
    return new WorkflowPage(
        store.findCompletedWorkflows(safeLimit, safeOffset),
        store.countCompletedWorkflows(),
        safeLimit,
        safeOffset);
  }

  public WorkflowPage completedWorkflows(int limit, int offset) {
    return workflows("completed", limit, offset);
  }

  static AuditEvent parse(Map<String, Object> body) {
    if (body == null || body.isEmpty()) {
      throw new AuditValidationException("body is required");
    }
    UUID eventId = parseUuid(body.get("event_id"), "event_id");
    String eventType = requiredString(body.get("event_type"), "event_type");
    Instant occurredAt = parseInstant(body.get("occurred_at"), "occurred_at");
    String producer = requiredString(body.get("producer"), "producer").toLowerCase(Locale.ROOT);
    if (!PRODUCERS.contains(producer)) {
      throw new AuditValidationException("producer must be afd|adp|ar|acr");
    }
    Object payloadRaw = body.get("payload");
    if (!(payloadRaw instanceof Map<?, ?> payloadMap)) {
      throw new AuditValidationException("payload must be an object");
    }
    Map<String, Object> payload = copyPayload(payloadMap);
    rejectDeniedKeys(payload);
    return new AuditEvent(
        eventId,
        eventType,
        occurredAt,
        producer,
        optionalString(body.get("correlation_id")),
        optionalString(body.get("session_id")),
        optionalString(body.get("decision_id")),
        payload);
  }

  private static Map<String, Object> copyPayload(Map<?, ?> raw) {
    Map<String, Object> out = new LinkedHashMap<>();
    for (Map.Entry<?, ?> e : raw.entrySet()) {
      if (e.getKey() == null) {
        continue;
      }
      out.put(String.valueOf(e.getKey()), e.getValue());
    }
    return out;
  }

  private static void rejectDeniedKeys(Map<String, Object> payload) {
    for (String key : payload.keySet()) {
      if (DENY_PAYLOAD_KEYS.contains(key.toLowerCase(Locale.ROOT))) {
        throw new AuditValidationException("payload key denied: " + key);
      }
    }
  }

  private static UUID parseUuid(Object raw, String field) {
    try {
      return UUID.fromString(requiredString(raw, field));
    } catch (IllegalArgumentException ex) {
      throw new AuditValidationException(field + " must be a UUID");
    }
  }

  private static Instant parseInstant(Object raw, String field) {
    try {
      return Instant.parse(requiredString(raw, field));
    } catch (Exception ex) {
      throw new AuditValidationException(field + " must be ISO-8601");
    }
  }

  private static String requiredString(Object raw, String field) {
    if (raw == null) {
      throw new AuditValidationException(field + " is required");
    }
    String value = String.valueOf(raw).trim();
    if (value.isEmpty() || "null".equals(value)) {
      throw new AuditValidationException(field + " is required");
    }
    return value;
  }

  private static String optionalString(Object raw) {
    if (raw == null) {
      return null;
    }
    String value = String.valueOf(raw).trim();
    if (value.isEmpty() || "null".equals(value)) {
      return null;
    }
    return value;
  }
}
