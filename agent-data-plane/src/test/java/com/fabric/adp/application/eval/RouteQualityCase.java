package com.fabric.adp.application.eval;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record RouteQualityCase(
    String id,
    String routeId,
    String ingress,
    String channel,
    Map<String, Object> goal,
    Map<String, Object> claims,
    RouteQualityExpected expected,
    List<String> tags) {

  public RouteQualityCase {
    goal = goal == null ? Map.of() : Map.copyOf(goal);
    claims = claims == null ? Map.of() : Map.copyOf(claims);
    tags = tags == null ? List.of() : List.copyOf(tags);
  }
}
