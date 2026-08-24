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
    List<String> eligibleRoutes,
    String routerLayer,
    Long latencyMs) {

  public static final String LAYER_RULES = "rules";
  public static final String LAYER_RETRIEVE = "retrieve";
  public static final String LAYER_LLM = "llm";

  public static DecideResult route(RouteRow row, double confidence, List<String> eligible) {
    return new DecideResult(
        "route",
        row.intentLabel(),
        row.routeId(),
        row.routeVersion(),
        confidence,
        null,
        null,
        eligible,
        null,
        null);
  }

  public static DecideResult clarify(
      String prompt, List<Map<String, Object>> candidates, List<String> eligible) {
    return new DecideResult(
        "clarify", null, null, null, null, prompt, candidates, eligible, null, null);
  }

  public static DecideResult abstain(List<String> eligible) {
    return new DecideResult("abstain", null, null, null, null, null, null, eligible, null, null);
  }

  public DecideResult withRouterLayer(String layer) {
    return new DecideResult(
        outcome,
        intentLabel,
        routeId,
        routeVersion,
        confidence,
        clarifyPrompt,
        candidates,
        eligibleRoutes,
        layer,
        latencyMs);
  }

  public DecideResult withLatencyMs(long ms) {
    return new DecideResult(
        outcome,
        intentLabel,
        routeId,
        routeVersion,
        confidence,
        clarifyPrompt,
        candidates,
        eligibleRoutes,
        routerLayer,
        ms);
  }
}
