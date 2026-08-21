package com.fabric.adp.domain;

import java.util.List;
import java.util.Map;

public record DecideResult(
    String outcome,
    String intentLabel,
    String routeId,
    String routeVersion,
    Double confidence,
    String clarifyPrompt,
    List<Map<String, Object>> candidates,
    List<String> eligibleRoutes) {

  public static DecideResult route(RouteRow row, double confidence, List<String> eligible) {
    return new DecideResult(
        "route",
        row.intentLabel(),
        row.routeId(),
        row.routeVersion(),
        confidence,
        null,
        null,
        eligible);
  }

  public static DecideResult clarify(
      String prompt, List<Map<String, Object>> candidates, List<String> eligible) {
    return new DecideResult("clarify", null, null, null, null, prompt, candidates, eligible);
  }

  public static DecideResult abstain(List<String> eligible) {
    return new DecideResult("abstain", null, null, null, null, null, null, eligible);
  }
}
