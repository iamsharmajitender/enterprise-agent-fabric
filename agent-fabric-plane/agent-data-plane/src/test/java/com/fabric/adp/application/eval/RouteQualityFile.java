package com.fabric.adp.application.eval;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record RouteQualityFile(
    String suiteId, String suiteVersion, List<RouteQualityCase> cases) {

  public RouteQualityFile {
    cases = cases == null ? List.of() : List.copyOf(cases);
  }
}
