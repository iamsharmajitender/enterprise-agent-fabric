package com.fabric.registry.bootstrap;

import io.opentelemetry.api.trace.Span;

/** Put allowlisted correlation fields on the current span. Not metric labels. */
public final class TraceIds {

  private TraceIds() {}

  public static void put(String key, String value) {
    if (value == null || value.isBlank()) {
      return;
    }
    Span.current().setAttribute(key, value);
  }
}
