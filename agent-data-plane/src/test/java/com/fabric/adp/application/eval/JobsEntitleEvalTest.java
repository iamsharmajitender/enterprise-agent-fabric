package com.fabric.adp.application.eval;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.CatalogueService;
import com.fabric.adp.application.DecideService;
import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.application.BusinessEvents;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.util.stream.Stream;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

class JobsEntitleEvalTest {

  private static final EvalFile FILE = EvalJson.load("/eval/jobs-entitle-golden.json");

  private DecideService decide;

  @BeforeEach
  void setUp() {
    decide =
        new DecideService(
            new CatalogueService(new InMemoryRouteStore().seedDemo()),
            new BusinessEvents(new SimpleMeterRegistry()));
  }

  @ParameterizedTest(name = "{0}")
  @MethodSource("cases")
  void jobsEntitle(String id, EvalCase evalCase) {
    assertThat(evalCase.ingress()).isEqualTo("jobs");
    assertThat(evalCase.message()).isNull();
    assertThat(evalCase.expected().outcome()).isNotEqualTo("clarify");
    DecideResult result =
        decide.decide(
            new DecideRequest(
                evalCase.ingress(),
                evalCase.channel(),
                "eval-" + id,
                evalCase.message(),
                evalCase.routeId(),
                evalCase.claims()),
            "afd");
    assertThat(result.outcome()).isEqualTo(evalCase.expected().outcome());
    if ("route".equals(evalCase.expected().outcome())) {
      assertThat(result.routeId()).isEqualTo(evalCase.expected().routeId());
      assertThat(result.confidence()).isEqualTo(1.0);
      if (evalCase.expected().routeVersion() != null) {
        assertThat(result.routeVersion()).isEqualTo(evalCase.expected().routeVersion());
      }
    } else {
      assertThat(result.routeId()).isNull();
    }
  }

  static Stream<Arguments> cases() {
    return FILE.cases().stream().map(evalCase -> Arguments.of(evalCase.id(), evalCase));
  }

  @Test
  void hiddenClaimsAdjudicateEntitlesWhenClaimed() {
    EvalCase entitled =
        FILE.cases().stream()
            .filter(c -> "jobs-claims_adjudicate-entitled".equals(c.id()))
            .findFirst()
            .orElseThrow();
    DecideResult result =
        decide.decide(
            new DecideRequest(
                "jobs", "web", "eval-hidden", null, "claims_adjudicate", entitled.claims()),
            "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("claims_adjudicate");
  }
}
