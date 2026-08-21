package com.fabric.afd.domain;

public record FrozenRoute(
    String sessionId,
    String idempotencyKey,
    String routeId,
    String routeVersion,
    String activationTarget,
    String agentClientId,
    String correlationId) {}
