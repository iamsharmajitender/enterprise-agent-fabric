package com.fabric.afd.domain;

import java.util.Map;

public record RunStart(
    String idempotencyKey, String sessionId, CatalogRoute route, Map<String, Object> payload) {}
