package com.fabric.afd.application;

import com.fabric.afd.domain.FrozenRoute;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class InMemoryFreezeStore implements FreezeStore {

  static final Duration TTL = Duration.ofMinutes(45);

  private final Map<String, Entry> bySession = new ConcurrentHashMap<>();
  private final Map<String, Opaque> opaques = new ConcurrentHashMap<>();

  @Override
  public void save(FrozenRoute freeze) {
    bySession.put(freeze.sessionId(), new Entry(freeze, Instant.now().plus(TTL)));
  }

  @Override
  public FrozenRoute get(String sessionId) {
    Entry entry = bySession.get(sessionId);
    if (entry == null || Instant.now().isAfter(entry.expiresAt())) {
      return null;
    }
    return entry.freeze();
  }

  @Override
  public FrozenRoute findByCorrelationId(String correlationId) {
    if (correlationId == null || correlationId.isBlank()) {
      return null;
    }
    Instant now = Instant.now();
    for (Entry entry : bySession.values()) {
      if (now.isAfter(entry.expiresAt())) {
        continue;
      }
      FrozenRoute freeze = entry.freeze();
      if (correlationId.equals(freeze.correlationId())) {
        return freeze;
      }
    }
    return null;
  }

  @Override
  public void putOpaque(String sessionId, String opaqueId, String routeId) {
    opaques.put(key(sessionId, opaqueId), new Opaque(routeId, Instant.now().plus(TTL)));
  }

  @Override
  public String resolveOpaque(String sessionId, String opaqueId) {
    Opaque opaque = opaques.get(key(sessionId, opaqueId));
    if (opaque == null || Instant.now().isAfter(opaque.expiresAt())) {
      return null;
    }
    return opaque.routeId();
  }

  public void expire(String sessionId) {
    Entry entry = bySession.get(sessionId);
    if (entry != null) {
      bySession.put(sessionId, new Entry(entry.freeze(), Instant.EPOCH));
    }
  }

  private static String key(String sessionId, String opaqueId) {
    return sessionId + "\0" + opaqueId;
  }

  private record Entry(FrozenRoute freeze, Instant expiresAt) {}

  private record Opaque(String routeId, Instant expiresAt) {}
}
