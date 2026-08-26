package com.fabric.afd.application;

import java.util.Map;

public interface AuditPort {
  AuditPort NOOP = event -> {};

  void emitAsync(Map<String, Object> event);
}
