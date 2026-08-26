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
    assertEquals(3, page.total());
    assertEquals(1, page.items().size());
    assertEquals("corr-c", page.items().get(0).correlationId());
    assertEquals(Instant.parse("2026-08-26T03:00:00Z"), page.items().get(0).completedAt());

    AuditEventService.WorkflowPage page2 = service.completedWorkflows(1, 1);
    assertEquals("corr-b", page2.items().get(0).correlationId());
    assertEquals("failed", page2.items().get(0).status());

    AuditEventService.WorkflowPage page3 = service.completedWorkflows(1, 2);
    assertEquals("corr-a", page3.items().get(0).correlationId());
    assertEquals(Instant.parse("2026-08-26T01:00:00Z"), page3.items().get(0).startedAt());
  }

  @Test
  void listCompletedWorkflowsSurfacesParentCorrelationId() {
    InMemoryStore store = new InMemoryStore();
    AuditEventService service = new AuditEventService(store);
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111301",
            "event_type",
            "freeze.written",
            "occurred_at",
            "2026-08-26T05:00:00Z",
            "producer",
            "afd",
            "correlation_id",
            "corr-child",
            "session_id",
            "sub-1",
            "payload",
            Map.of(
                "route_id",
                "policy_refund",
                "route_version",
                "2026.08.1",
                "ingress",
                "jobs",
                "parent_correlation_id",
                "corr-parent")));
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111302",
            "event_type",
            "run.terminal",
            "occurred_at",
            "2026-08-26T05:01:00Z",
            "producer",
            "ar",
            "correlation_id",
            "corr-child",
            "session_id",
            "sub-1",
            "payload",
            Map.of("status", "completed", "route_id", "policy_refund", "route_version", "2026.08.1")));

    AuditEventService.WorkflowPage page = service.completedWorkflows(10, 0);
    assertEquals(1, page.total());
    assertEquals("corr-parent", page.items().get(0).parentCorrelationId());
  }

  @Test
  void listInProgressWorkflowsIncludesWaitingAndRunning() {
    InMemoryStore store = new InMemoryStore();
    AuditEventService service = new AuditEventService(store);
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111201",
            "event_type",
            "hydrate.snapshot",
            "occurred_at",
            "2026-08-26T04:00:00Z",
            "producer",
            "ar",
            "correlation_id",
            "corr-run",
            "session_id",
            "sess-run",
            "payload",
            Map.of("route_id", "shopassist_case", "route_version", "2026.08.1")));
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111202",
            "event_type",
            "run.terminal",
            "occurred_at",
            "2026-08-26T04:05:00Z",
            "producer",
            "ar",
            "correlation_id",
            "corr-wait",
            "session_id",
            "sess-wait",
            "payload",
            Map.of("status", "waiting", "route_id", "shopassist_case", "route_version", "2026.08.1")));
    service.ingest(
        Map.of(
            "event_id",
            "11111111-1111-4111-8111-111111111203",
            "event_type",
            "run.terminal",
            "occurred_at",
            "2026-08-26T04:10:00Z",
            "producer",
            "ar",
            "correlation_id",
            "corr-done",
            "payload",
            Map.of("status", "completed", "route_id", "fee_explain")));

    AuditEventService.WorkflowPage page = service.workflows("in_progress", 10, 0);
    assertEquals(2, page.total());
    assertEquals("corr-wait", page.items().get(0).correlationId());
    assertEquals("waiting", page.items().get(0).status());
    assertEquals("corr-run", page.items().get(1).correlationId());
    assertEquals("running", page.items().get(1).status());
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
        if (!"completed".equals(String.valueOf(status)) && !"failed".equals(String.valueOf(status))) {
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
                    e.occurredAt(),
                    parentOf(e.correlationId()));
              })
          .toList();
    }

    @Override
    public long countCompletedWorkflows() {
      return byId.values().stream()
          .filter(e -> "run.terminal".equals(e.eventType()))
          .filter(e -> e.correlationId() != null)
          .filter(
              e -> {
                String status = String.valueOf(e.payload().get("status"));
                return "completed".equals(status) || "failed".equals(status);
              })
          .map(AuditEvent::correlationId)
          .distinct()
          .count();
    }

    private String parentOf(String correlationId) {
      return findByCorrelationId(correlationId).stream()
          .map(e -> e.payload().get("parent_correlation_id"))
          .filter(Objects::nonNull)
          .map(String::valueOf)
          .map(String::trim)
          .filter(s -> !s.isEmpty() && !"null".equals(s))
          .findFirst()
          .orElse(null);
    }

    @Override
    public List<CompletedWorkflow> findInProgressWorkflows(int limit, int offset) {
      return openRuns().stream()
          .sorted(Comparator.comparing(CompletedWorkflow::completedAt).reversed())
          .skip(offset)
          .limit(limit)
          .toList();
    }

    @Override
    public long countInProgressWorkflows() {
      return openRuns().size();
    }

    private List<CompletedWorkflow> openRuns() {
      Map<String, Instant> started = new ConcurrentHashMap<>();
      Map<String, Instant> last = new ConcurrentHashMap<>();
      Map<String, AuditEvent> latestTerminal = new ConcurrentHashMap<>();
      Map<String, AuditEvent> meta = new ConcurrentHashMap<>();
      for (AuditEvent e : byId.values()) {
        if (e.correlationId() == null) {
          continue;
        }
        started.merge(e.correlationId(), e.occurredAt(), (a, b) -> a.isBefore(b) ? a : b);
        last.merge(e.correlationId(), e.occurredAt(), (a, b) -> a.isAfter(b) ? a : b);
        if ("run.terminal".equals(e.eventType())) {
          AuditEvent prev = latestTerminal.get(e.correlationId());
          if (prev == null || e.occurredAt().isAfter(prev.occurredAt())) {
            latestTerminal.put(e.correlationId(), e);
          }
        }
        if (List.of("hydrate.snapshot", "freeze.written", "run.terminal", "decide.completed")
            .contains(e.eventType())) {
          AuditEvent prev = meta.get(e.correlationId());
          if (prev == null || preferMeta(e, prev)) {
            meta.put(e.correlationId(), e);
          }
        }
      }
      List<CompletedWorkflow> out = new java.util.ArrayList<>();
      for (String corr : started.keySet()) {
        AuditEvent terminal = latestTerminal.get(corr);
        String status =
            terminal == null
                ? "running"
                : Objects.toString(terminal.payload().get("status"), "running");
        if (terminal != null && ("completed".equals(status) || "failed".equals(status))) {
          continue;
        }
        AuditEvent m = meta.get(corr);
        Map<String, Object> payload =
            terminal != null
                ? terminal.payload()
                : m != null ? m.payload() : Map.of();
        out.add(
            new CompletedWorkflow(
                corr,
                terminal != null
                    ? terminal.sessionId()
                    : m != null ? m.sessionId() : null,
                terminal != null
                    ? terminal.decisionId()
                    : m != null ? m.decisionId() : null,
                Objects.toString(payload.get("route_id"), null),
                Objects.toString(payload.get("route_version"), null),
                status,
                started.get(corr),
                last.get(corr),
                parentOf(corr)));
      }
      return out;
    }

    private static boolean preferMeta(AuditEvent candidate, AuditEvent existing) {
      int c = metaRank(candidate.eventType());
      int e = metaRank(existing.eventType());
      if (c != e) {
        return c < e;
      }
      return candidate.occurredAt().isAfter(existing.occurredAt());
    }

    private static int metaRank(String type) {
      return switch (type) {
        case "run.terminal" -> 0;
        case "hydrate.snapshot" -> 1;
        case "freeze.written" -> 2;
        default -> 3;
      };
    }
  }
}
