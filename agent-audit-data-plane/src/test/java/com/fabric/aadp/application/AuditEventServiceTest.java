package com.fabric.aadp.application;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fabric.aadp.domain.AuditEvent;
import com.fabric.aadp.domain.AuditValidationException;
import com.fabric.aadp.domain.CompletedWorkflow;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.junit.jupiter.api.Test;

class AuditEventServiceTest {

  @Test
  void ingestIdempotentAndQuery() {
    InMemoryStore store = new InMemoryStore();
    AuditEventService service = new AuditEventService(store);
    Map<String, Object> body =
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111111",
            "event_type",
            "decide.completed",
            "occurred_at",
            "2026-08-26T01:00:00Z",
            "producer",
            "adp",
            "correlation_id",
            "corr-1",
            "session_id",
            "sess-1",
            "payload",
            Map.of("outcome", "route", "route_id", "fee_explain"));
    AuditEvent first = service.ingest(body);
    AuditEvent second = service.ingest(body);
    assertEquals(first.eventId(), second.eventId());
    assertEquals(1, store.byId.size());
    assertEquals(1, service.chain("corr-1").size());
    assertEquals(1, service.session("sess-1").size());
  }

  @Test
  void rejectDeniedPayload() {
    AuditEventService service = new AuditEventService(new InMemoryStore());
    Map<String, Object> body =
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111112",
            "event_type",
            "decide.completed",
            "occurred_at",
            "2026-08-26T01:00:00Z",
            "producer",
            "adp",
            "payload",
            Map.of("utterance", "secret"));
    assertThrows(AuditValidationException.class, () -> service.ingest(body));
  }

  @Test
  void healthUp() {
    assertEquals("UP", new HealthService().current().status());
  }

  @Test
  void listCompletedWorkflowsPaginated() {
    InMemoryStore store = new InMemoryStore();
    AuditEventService service = new AuditEventService(store);
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111101",
            "event_type",
            "hydrate.snapshot",
            "occurred_at",
            "2026-08-26T01:00:00Z",
            "producer",
            "ar",
            "correlation_id",
            "corr-a",
            "session_id",
            "sess-a",
            "payload",
            Map.of("route_id", "email_summarize")));
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111102",
            "event_type",
            "run.terminal",
            "occurred_at",
            "2026-08-26T01:00:10Z",
            "producer",
            "ar",
            "correlation_id",
            "corr-a",
            "session_id",
            "sess-a",
            "payload",
            Map.of("status", "completed", "route_id", "email_summarize", "route_version", "1")));
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111103",
            "event_type",
            "run.terminal",
            "occurred_at",
            "2026-08-26T02:00:00Z",
            "producer",
            "ar",
            "correlation_id",
            "corr-b",
            "payload",
            Map.of("status", "failed", "route_id", "fee_explain")));
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111104",
            "event_type",
            "run.terminal",
            "occurred_at",
            "2026-08-26T03:00:00Z",
            "producer",
            "ar",
            "correlation_id",
            "corr-c",
            "payload",
            Map.of("status", "completed", "route_id", "fee_explain", "route_version", "2")));

    AuditEventService.WorkflowPage page = service.completedWorkflows(1, 0);
    assertEquals(2, page.total());
    assertEquals(1, page.items().size());
    assertEquals("corr-c", page.items().get(0).correlationId());
    assertEquals(Instant.parse("2026-08-26T03:00:00Z"), page.items().get(0).completedAt());

    AuditEventService.WorkflowPage page2 = service.completedWorkflows(1, 1);
    assertEquals("corr-a", page2.items().get(0).correlationId());
    assertEquals(Instant.parse("2026-08-26T01:00:00Z"), page2.items().get(0).startedAt());
  }

  static final class InMemoryStore implements AuditEventStore {
    final ConcurrentHashMap<UUID, AuditEvent> byId = new ConcurrentHashMap<>();

    @Override
    public boolean insertIdempotent(AuditEvent event) {
      return byId.putIfAbsent(event.eventId(), event) == null;
    }

    @Override
    public Optional<AuditEvent> findById(UUID eventId) {
      return Optional.ofNullable(byId.get(eventId));
    }

    @Override
    public List<AuditEvent> findByCorrelationId(String correlationId) {
      return byId.values().stream()
          .filter(e -> correlationId.equals(e.correlationId()))
          .sorted(Comparator.comparing(AuditEvent::occurredAt))
          .toList();
    }

    @Override
    public List<AuditEvent> findBySessionId(String sessionId) {
      return byId.values().stream()
          .filter(e -> sessionId.equals(e.sessionId()))
          .sorted(Comparator.comparing(AuditEvent::occurredAt))
          .toList();
    }

    @Override
    public List<CompletedWorkflow> findCompletedWorkflows(int limit, int offset) {
      Map<String, AuditEvent> latest = new ConcurrentHashMap<>();
      for (AuditEvent e : byId.values()) {
        if (!"run.terminal".equals(e.eventType()) || e.correlationId() == null) {
          continue;
        }
        Object status = e.payload().get("status");
        if (!"completed".equals(String.valueOf(status))) {
          continue;
        }
        AuditEvent prev = latest.get(e.correlationId());
        if (prev == null || e.occurredAt().isAfter(prev.occurredAt())) {
          latest.put(e.correlationId(), e);
        }
      }
      return latest.values().stream()
          .sorted(Comparator.comparing(AuditEvent::occurredAt).reversed())
          .skip(offset)
          .limit(limit)
          .map(
              e -> {
                Instant started =
                    findByCorrelationId(e.correlationId()).stream()
                        .map(AuditEvent::occurredAt)
                        .min(Comparator.naturalOrder())
                        .orElse(e.occurredAt());
                return new CompletedWorkflow(
                    e.correlationId(),
                    e.sessionId(),
                    e.decisionId(),
                    Objects.toString(e.payload().get("route_id"), null),
                    Objects.toString(e.payload().get("route_version"), null),
                    Objects.toString(e.payload().get("status"), null),
                    started,
                    e.occurredAt());
              })
          .toList();
    }

    @Override
    public long countCompletedWorkflows() {
      return byId.values().stream()
          .filter(e -> "run.terminal".equals(e.eventType()))
          .filter(e -> e.correlationId() != null)
          .filter(e -> "completed".equals(String.valueOf(e.payload().get("status"))))
          .map(AuditEvent::correlationId)
          .distinct()
          .count();
    }
  }
}
