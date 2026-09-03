package com.fabric.adp.application.eval;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.BusinessEvents;
import com.fabric.adp.application.CatalogueService;
import com.fabric.adp.application.DecideService;
import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.RouteRow;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

class RoutingEvalTest {

  private static final EvalFile FILE = EvalJson.loadActive("routing");

  private DecideService decide;
  private CatalogueService catalogue;

  @BeforeEach
  void setUp() {
    catalogue = new CatalogueService(new InMemoryRouteStore().seedEvalBoard());
    decide = new DecideService(catalogue, new BusinessEvents(new SimpleMeterRegistry()));
  }

  @Test
  void goldenCatalogueMatchesInMemorySeed() {
    Set<String> labelled =
        FILE.catalogue().stream().map(EvalCataloguePin::routeId).collect(Collectors.toSet());
    Set<String> seeded =
        catalogue.listAll().stream().map(RouteRow::routeId).collect(Collectors.toSet());
    assertThat(labelled).isEqualTo(seeded);
    assertThat(FILE.catalogue()).allMatch(pin -> "2026.08.1".equals(pin.routeVersion()));
  }

  @ParameterizedTest(name = "{0}")
  @MethodSource("cases")
  void chatRouting(String id, EvalCase evalCase) {
    assertThat(evalCase.ingress()).isEqualTo("chat");
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
      if (evalCase.expected().routeVersion() != null) {
        assertThat(result.routeVersion()).isEqualTo(evalCase.expected().routeVersion());
      }
      // Hidden / jobs-only routes must never win chat classify.
      assertThat(result.routeId()).isNotIn("kyc_onboarding", "ticket_draft_reply");
    } else {
      assertThat(result.routeId()).isNull();
    }
  }

  static Stream<Arguments> cases() {
    return FILE.cases().stream().map(evalCase -> Arguments.of(evalCase.id(), evalCase));
  }

  @Test
  void everyCaseIdIsUnique() {
    List<String> ids = FILE.cases().stream().map(EvalCase::id).toList();
    assertThat(new HashSet<>(ids)).hasSize(ids.size());
  }
}
