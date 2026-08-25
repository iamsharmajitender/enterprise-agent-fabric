package com.fabric.adp.application.eval;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record RouteQualityExpected(List<RouteQualityStageExpect> stages) {

  public RouteQualityExpected {
    stages = stages == null ? List.of() : List.copyOf(stages);
  }
}
