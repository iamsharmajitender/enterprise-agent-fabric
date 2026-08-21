package com.fabric.afd.domain;

import java.util.Map;

public record DecideCall(
    String ingress,
    String channel,
    String sessionId,
    String message,
    String routeId,
    Map<String, Object> claims) {}
