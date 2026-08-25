package com.fabric.adp.application.eval;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record EvalFile(
    String suiteId,
    String suiteVersion,
    List<EvalCataloguePin> catalogue,
    List<EvalCase> cases) {

  public EvalFile {
    catalogue = catalogue == null ? List.of() : List.copyOf(catalogue);
    cases = cases == null ? List.of() : List.copyOf(cases);
  }
}
