package com.fabric.aadp.domain;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record AuditEvent(
    UUID eventId,
    String eventType,
    Instant occurredAt,
    String producer,
    String correlationId,
    String sessionId,
    String decisionId,
    Map<String, Object> payload) {}
