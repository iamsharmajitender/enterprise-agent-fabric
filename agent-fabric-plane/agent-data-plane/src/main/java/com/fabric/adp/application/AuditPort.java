package com.fabric.adp.application;

import java.util.Map;

/** Fire-and-forget fabric audit emit. Never throws to callers. */
public interface AuditPort {
  AuditPort NOOP = event -> {};

  void emitAsync(Map<String, Object> event);
}
