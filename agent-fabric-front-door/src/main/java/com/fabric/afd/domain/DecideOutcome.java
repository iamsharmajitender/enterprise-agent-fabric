package com.fabric.afd.domain;

import java.util.List;
import java.util.Map;

public record DecideOutcome(
    String outcome,
    String routeId,
    String routeVersion,
    String clarifyPrompt,
    List<Map<String, Object>> candidates) {

  public DecideOutcome {
    candidates = candidates == null ? List.of() : List.copyOf(candidates);
  }

  public DecideOutcome(String outcome, String routeId, String routeVersion) {
    this(outcome, routeId, routeVersion, null, List.of());
  }

  public boolean routed() {
    return "route".equals(outcome);
  }
}
