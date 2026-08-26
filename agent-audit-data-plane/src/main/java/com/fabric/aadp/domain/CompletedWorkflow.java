package com.fabric.aadp.domain;

import java.time.Instant;

/** One finished run (correlation) that reached {@code run.terminal} with status completed. */
public record CompletedWorkflow(
    String correlationId,
    String sessionId,
    String decisionId,
    String routeId,
    String routeVersion,
    String status,
    Instant startedAt,
    Instant completedAt) {}
