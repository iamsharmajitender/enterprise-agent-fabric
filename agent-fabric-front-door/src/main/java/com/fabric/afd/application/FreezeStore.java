package com.fabric.afd.application;

import com.fabric.afd.domain.FrozenRoute;

public interface FreezeStore {
  void save(FrozenRoute freeze);

  FrozenRoute get(String sessionId);

  FrozenRoute findByCorrelationId(String correlationId);

  void putOpaque(String sessionId, String opaqueId, String routeId);

  String resolveOpaque(String sessionId, String opaqueId);
}
