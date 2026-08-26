package com.fabric.aadp.domain;

import java.time.Instant;

/**
 * One run (correlation) for the workflows list. {@code completedAt} is the terminal time for
 * finished runs, or the latest activity time for in-progress runs. {@code parentCorrelationId} is
 * set when this run was started as a {@code kind=agent} child of another correlation.
 */
public record CompletedWorkflow(
    String correlationId,
    String sessionId,
    String decisionId,
    String routeId,
    String routeVersion,
    String status,
    Instant startedAt,
    Instant completedAt,
    String parentCorrelationId) {}
