package com.fabric.adp.application.eval;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record EvalCase(
    String id,
    String ingress,
    String channel,
    String message,
    String routeId,
    Map<String, Object> claims,
    EvalExpected expected,
    List<String> tags) {

  public EvalCase {
    claims = claims == null ? Map.of() : Map.copyOf(claims);
    tags = tags == null ? List.of() : List.copyOf(tags);
  }
}
