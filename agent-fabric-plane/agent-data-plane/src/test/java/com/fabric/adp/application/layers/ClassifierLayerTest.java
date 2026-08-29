package com.fabric.adp.application.layers;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.RiskClass;
import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class ClassifierLayerTest {

  private final InMemoryRouteStore store = new InMemoryRouteStore().seedDemo();
  private final ClassifierLayer classifier = new ClassifierLayer();

  @Test
  void seedMapsShopassistToMidRisk() {
    assertThat(row("shopassist_case").riskClass()).isEqualTo(RiskClass.MID);
  }

  @Test
  void shopassistUtteranceRoutesAtRetrieveConfidence() {
    Optional<DecideResult> result =
        classifier.apply(
            message("My blue jacket arrived damaged and I want a refund"),
            List.of(row("shopassist_case")));
    assertThat(result).isPresent();
    assertThat(result.get().outcome()).isEqualTo("route");
    assertThat(result.get().routeId()).isEqualTo("shopassist_case");
    assertThat(result.get().confidence()).isEqualTo(ClassifierLayer.RETRIEVE_CONFIDENCE);
  }

  @Test
  void unrelatedUtteranceAbstainsWithSingleRoute() {
    Optional<DecideResult> result =
        classifier.apply(message("hello there"), List.of(row("shopassist_case")));
    assertThat(result).isEmpty();
  }

  private RouteRow row(String routeId) {
    return store.activeRoute(routeId).orElseThrow();
  }

  private static DecideRequest message(String text) {
    return new DecideRequest("chat", "web", "sess-88", text, null, Map.of());
  }
}
