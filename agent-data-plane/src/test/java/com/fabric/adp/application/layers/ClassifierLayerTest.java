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
  void seedMapsPolicyToRiskClass() {
    assertThat(row("agent-chat").riskClass()).isEqualTo(RiskClass.LOW);
    assertThat(row("fee_explain").riskClass()).isEqualTo(RiskClass.MID);
    assertThat(row("card_freeze").riskClass()).isEqualTo(RiskClass.HIGH);
  }

  @Test
  void uniqueFeeHitRoutesAtRetrieveConfidence() {
    Optional<DecideResult> result =
        classifier.apply(message("Why was I charged $42?"), List.of(row("fee_explain")));
    assertThat(result).isPresent();
    assertThat(result.get().outcome()).isEqualTo("route");
    assertThat(result.get().routeId()).isEqualTo("fee_explain");
    assertThat(result.get().confidence()).isEqualTo(ClassifierLayer.RETRIEVE_CONFIDENCE);
  }

  @Test
  void uniqueHighRiskHitBelowBarClarifies() {
    Optional<DecideResult> result =
        classifier.apply(
            message("Please freeze this card"), List.of(row("fee_explain"), row("card_freeze")));
    assertThat(result).isPresent();
    assertThat(result.get().outcome()).isEqualTo("clarify");
    assertThat(result.get().routeId()).isNull();
    assertThat(result.get().candidates()).hasSize(1);
    assertThat(result.get().candidates().getFirst().get("route_id")).isEqualTo("card_freeze");
    assertThat(result.get().candidates().getFirst().get("confidence"))
        .isEqualTo(ClassifierLayer.RETRIEVE_CONFIDENCE);
  }

  @Test
  void keywordsOnTheRowAreNotScored() {
    RouteRow decoy =
        withKeywords(row("fee_explain"), List.of("freeze"));
    Optional<DecideResult> result =
        classifier.apply(message("Please freeze this card"), List.of(decoy, row("card_freeze")));
    assertThat(result).isPresent();
    assertThat(result.get().outcome()).isEqualTo("clarify");
    assertThat(result.get().candidates().getFirst().get("route_id")).isEqualTo("card_freeze");
  }

  private RouteRow row(String routeId) {
    return store.activeRoute(routeId).orElseThrow();
  }

  private static RouteRow withKeywords(RouteRow row, List<String> keywords) {
    return new RouteRow(
        row.routeId(),
        row.routeVersion(),
        row.active(),
        row.intentLabel(),
        row.description(),
        row.activationTarget(),
        row.agentClientId(),
        row.manifest(),
        row.policyProfile(),
        row.modelProfile(),
        row.retrieval(),
        row.memoryProfile(),
        row.workflowId(),
        row.promptId(),
        row.outputSchemaId(),
        row.evalSuiteId(),
        row.maxLoopSteps(),
        row.fallback(),
        row.requiredClaims(),
        row.channels(),
        row.chatVisible(),
        keywords,
        row.autonomyMode());
  }

  private static DecideRequest message(String text) {
    return new DecideRequest("chat", "web", "sess-88", text, null, Map.of());
  }
}
