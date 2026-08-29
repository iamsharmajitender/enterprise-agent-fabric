package com.fabric.aadp.application;

import com.fabric.aadp.domain.AuditEvent;
import com.fabric.aadp.domain.CompletedWorkflow;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface AuditEventStore {
  /** Insert if new; return true when inserted, false when event_id already present. */
  boolean insertIdempotent(AuditEvent event);

  Optional<AuditEvent> findById(UUID eventId);

  List<AuditEvent> findByCorrelationId(String correlationId);

  List<AuditEvent> findBySessionId(String sessionId);

  /** Completed runs newest-first; {@code limit}/{@code offset} for page windows. */
  List<CompletedWorkflow> findCompletedWorkflows(int limit, int offset);

  long countCompletedWorkflows();

  /**
   * In-progress runs newest-first: started correlations without a completed/failed terminal
   * (includes {@code waiting} and still-running).
   */
  List<CompletedWorkflow> findInProgressWorkflows(int limit, int offset);

  long countInProgressWorkflows();
}
