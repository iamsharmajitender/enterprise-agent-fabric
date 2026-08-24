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
        layer.apply(message("Why was I charged $42?"), List.of(row("fee_explain")));
    assertThat(result).isEmpty();
  }

  @Test
  void enabledStillHasNoLiveModel() {
    LlmFallbackLayer layer = new LlmFallbackLayer(true);
    assertThat(layer.enabled()).isTrue();
    assertThat(layer.apply(message("ambiguous"), List.of(row("fee_explain")))).isEmpty();
  }

  @Test
  void routeIdOutsideEligibleAbstains() {
    DecideResult proposed =
        DecideResult.route(row("card_freeze"), 0.5, List.of("fee_explain", "card_freeze"));
    DecideResult bound = LlmFallbackLayer.restrictToEligible(proposed, List.of(row("fee_explain")));
    assertThat(bound.outcome()).isEqualTo("abstain");
    assertThat(bound.routeId()).isNull();
    assertThat(bound.eligibleRoutes()).containsExactly("fee_explain");
  }

  @Test
  void routeIdInsideEligibleKeepsTheRow() {
    DecideResult proposed = DecideResult.route(row("fee_explain"), 0.5, List.of("fee_explain"));
    DecideResult bound = LlmFallbackLayer.restrictToEligible(proposed, List.of(row("fee_explain")));
    assertThat(bound.outcome()).isEqualTo("route");
    assertThat(bound.routeId()).isEqualTo("fee_explain");
  }

  @Test
  void clarifyDropsCandidatesOutsideEligible() {
    DecideResult proposed =
        DecideResult.clarify(
            "pick",
            List.of(
                Map.of("route_id", "card_freeze", "intent_label", "card_freeze"),
                Map.of("route_id", "fee_explain", "intent_label", "fee_explain")),
            List.of("fee_explain", "card_freeze"));
    DecideResult bound = LlmFallbackLayer.restrictToEligible(proposed, List.of(row("fee_explain")));
    assertThat(bound.outcome()).isEqualTo("clarify");
    assertThat(bound.candidates()).extracting(c -> c.get("route_id")).containsExactly("fee_explain");
  }

  private RouteRow row(String routeId) {
    return store.activeRoute(routeId).orElseThrow();
  }

  private static DecideRequest message(String text) {
    return new DecideRequest("chat", "web", "sess-88", text, null, Map.of());
  }
}
