package com.fabric.afd.application;

import io.micrometer.core.instrument.MeterRegistry;
import java.util.LinkedHashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

/** Layer ① business events + low-cardinality journey counters. No utterance or claims. */
public final class BusinessEvents {

  private static final Logger log = LoggerFactory.getLogger(BusinessEvents.class);

  private final MeterRegistry meters;

  public BusinessEvents(MeterRegistry meters) {
    this.meters = meters;
  }

  public void emit(String event, String journeyId, Map<String, String> fields) {
    Map<String, String> safe = fields == null ? Map.of() : fields;
    MDC.put("event", event);
    if (journeyId != null) {
      MDC.put("journey_id", journeyId);
    }
    safe.forEach(
        (k, v) -> {
          if (v != null && !v.isBlank()) {
            MDC.put(k, v);
          }
        });
    try {
      log.info("{}", event);
    } finally {
      MDC.remove("event");
      MDC.remove("journey_id");
      safe.keySet().forEach(MDC::remove);
    }
  }

  public void countOutcome(String journeyId, String outcome, String channel) {
    meters
        .counter(
            "fabric_journey_outcome_total",
            "journey_id",
            nullToUnknown(journeyId),
            "outcome",
            nullToUnknown(outcome),
            "channel",
            nullToUnknown(channel))
        .increment();
  }

  public static Map<String, String> fields(String... kv) {
    if (kv.length % 2 != 0) {
      throw new IllegalArgumentException("even number of args required");
    }
    Map<String, String> map = new LinkedHashMap<>();
    for (int i = 0; i < kv.length; i += 2) {
      if (kv[i + 1] != null) {
        map.put(kv[i], kv[i + 1]);
      }
    }
    return map;
  }

  private static String nullToUnknown(String value) {
    return value == null || value.isBlank() ? "unknown" : value;
  }
}
