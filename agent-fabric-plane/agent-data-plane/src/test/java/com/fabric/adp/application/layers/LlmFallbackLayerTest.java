package com.fabric.adp.application.layers;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class LlmFallbackLayerTest {

  private final InMemoryRouteStore store = new InMemoryRouteStore().seedDemo();

  @Test
  void defaultOffAndApplyIsEmpty() {
    LlmFallbackLayer layer = new LlmFallbackLayer();
    assertThat(layer.enabled()).isFalse();
    Optional<DecideResult> result =
        layer.apply(
            message("My blue jacket arrived damaged and I want a refund"),
            List.of(row("shopassist_case")));
    assertThat(result).isEmpty();
  }

  @Test
  void enabledStillHasNoLiveModel() {
    LlmFallbackLayer layer = new LlmFallbackLayer(true);
    assertThat(layer.enabled()).isTrue();
    assertThat(layer.apply(message("ambiguous"), List.of(row("shopassist_case")))).isEmpty();
  }

  @Test
  void routeIdInsideEligibleKeepsTheRow() {
    DecideResult proposed =
        DecideResult.route(row("shopassist_case"), 0.5, List.of("shopassist_case"));
    DecideResult bound =
        LlmFallbackLayer.restrictToEligible(proposed, List.of(row("shopassist_case")));
    assertThat(bound.outcome()).isEqualTo("route");
    assertThat(bound.routeId()).isEqualTo("shopassist_case");
  }

  private RouteRow row(String routeId) {
    return store.activeRoute(routeId).orElseThrow();
  }

  private static DecideRequest message(String text) {
    return new DecideRequest("chat", "web", "sess-88", text, null, Map.of());
  }
}
