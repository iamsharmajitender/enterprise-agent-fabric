package com.fabric.adp.domain;

import java.util.Map;
import java.util.Set;

public record DecideRequest(
    String ingress,
    String channel,
    String sessionId,
    String message,
    String routeId,
    Map<String, Object> claims) {

  public Set<String> entitledClaims() {
    if (claims == null) {
      return Set.of();
    }
    Object emts = claims.get("emts");
    if (!(emts instanceof Map<?, ?> map)) {
      return Set.of();
    }
    return map.entrySet().stream()
        .filter(e -> Boolean.TRUE.equals(e.getValue()))
        .map(e -> String.valueOf(e.getKey()))
        .collect(java.util.stream.Collectors.toSet());
  }

  public boolean hasRouteId() {
    return routeId != null && !routeId.isBlank();
  }
}
