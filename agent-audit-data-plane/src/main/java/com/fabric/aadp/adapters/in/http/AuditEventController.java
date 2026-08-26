package com.fabric.aadp.adapters.in.http;

import com.fabric.aadp.application.AuditEventService;
import com.fabric.aadp.domain.AuditEvent;
import com.fabric.aadp.domain.AuditValidationException;
import com.fabric.aadp.domain.CompletedWorkflow;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AuditEventController {

  private final AuditEventService events;

  public AuditEventController(AuditEventService events) {
    this.events = events;
  }

  @PostMapping("/v1/audit/events")
  public ResponseEntity<Map<String, Object>> ingest(@RequestBody Map<String, Object> body) {
    AuditEvent saved = events.ingest(body);
    return ResponseEntity.status(HttpStatus.OK).body(toMap(saved));
  }

  @GetMapping("/v1/audit/chains/{correlationId}")
  public List<Map<String, Object>> chain(@PathVariable String correlationId) {
    return events.chain(correlationId).stream().map(AuditEventController::toMap).toList();
  }

  @GetMapping("/v1/audit/sessions/{sessionId}")
  public List<Map<String, Object>> session(@PathVariable String sessionId) {
    return events.session(sessionId).stream().map(AuditEventController::toMap).toList();
  }

  @GetMapping("/v1/audit/workflows")
  public Map<String, Object> workflows(
      @RequestParam(defaultValue = "50") int limit,
      @RequestParam(defaultValue = "0") int offset,
      @RequestParam(defaultValue = "completed") String status) {
    AuditEventService.WorkflowPage page = events.workflows(status, limit, offset);
    Map<String, Object> out = new LinkedHashMap<>();
    out.put("items", page.items().stream().map(AuditEventController::toWorkflowMap).toList());
    out.put("total", page.total());
    out.put("limit", page.limit());
    out.put("offset", page.offset());
    out.put("status", "in_progress".equalsIgnoreCase(status) || "in-progress".equalsIgnoreCase(status)
        ? "in_progress"
        : "completed");
    return out;
  }

  @ExceptionHandler(AuditValidationException.class)
  public ResponseEntity<Map<String, Object>> validation(AuditValidationException ex) {
    return ResponseEntity.badRequest()
        .body(Map.of("error", Map.of("code", "VALIDATION", "message", ex.getMessage())));
  }

  static Map<String, Object> toMap(AuditEvent event) {
    Map<String, Object> out = new LinkedHashMap<>();
    out.put("event_id", event.eventId().toString());
    out.put("event_type", event.eventType());
    out.put("occurred_at", event.occurredAt().toString());
    out.put("producer", event.producer());
    out.put("correlation_id", event.correlationId());
    out.put("session_id", event.sessionId());
    out.put("decision_id", event.decisionId());
    out.put("payload", event.payload());
    return out;
  }

  static Map<String, Object> toWorkflowMap(CompletedWorkflow workflow) {
    Map<String, Object> out = new LinkedHashMap<>();
    out.put("correlation_id", workflow.correlationId());
    out.put("session_id", workflow.sessionId());
    out.put("decision_id", workflow.decisionId());
    out.put("route_id", workflow.routeId());
    out.put("route_version", workflow.routeVersion());
    out.put("status", workflow.status());
    out.put("started_at", workflow.startedAt().toString());
    out.put("completed_at", workflow.completedAt().toString());
    out.put("parent_correlation_id", workflow.parentCorrelationId());
    return out;
  }
}
