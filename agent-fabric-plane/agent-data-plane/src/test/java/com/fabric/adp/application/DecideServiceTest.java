package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.layers.DecideLayer;
import com.fabric.adp.application.layers.LlmFallbackLayer;
import com.fabric.adp.application.layers.LlmFallbackPool;
import com.fabric.adp.application.layers.RulesLayer;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class DecideServiceTest {

  private DecideService decide;

  @BeforeEach
  void setUp() {
    decide =
        new DecideService(
            new CatalogueService(new InMemoryRouteStore().seedDemo()),
            new BusinessEvents(new SimpleMeterRegistry()),
            demoRules());
  }

  @Test
  void shopassistUtteranceRoutesToShopassistCase() {
    DecideResult result =
        decide.decide(chat("My blue jacket arrived damaged and I want a refund", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("shopassist_case");
    assertThat(result.routeVersion()).isEqualTo("2026.08.1");
    assertThat(result.confidence()).isEqualTo(0.91);
    assertLayer(result, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void emptyEligibleAbstains() {
    DecideResult result =
        decide.decide(
            new DecideRequest(
                "chat",
                "sms",
                "s",
                "My blue jacket arrived damaged and I want a refund",
                null,
                jane()),
            "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertLayer(result, null);
  }

  @Test
  void explicitRouteIdBindsWithoutKeywords() {
    DecideResult result =
        decide.decide(
            new DecideRequest("jobs", "web", "job:1", null, "shopassist_case", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("shopassist_case");
    assertThat(result.confidence()).isEqualTo(1.0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void slashCommandRoutesShopassist() {
    // Layer ① command rules match the full message (exact), not a prefix.
    DecideResult result = decide.decide(chat("/shopassist", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("shopassist_case");
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void unrelatedUtteranceAbstains() {
    DecideResult result = decide.decide(chat("xyzzy-no-such-intent", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertThat(result.routeId()).isNull();
    assertLayer(result, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void jobsBodyDoesNotParseChatSlash() {
    AtomicInteger classifierCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), new LlmFallbackLayer())
            .decide(
                new DecideRequest("jobs", "web", "job:1", "/shopassist", "shopassist_case", jane()),
                "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("shopassist_case");
    assertThat(classifierCalls).hasValue(0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  private static void assertLayer(DecideResult result, String layer) {
    assertThat(result.routerLayer()).isEqualTo(layer);
    assertThat(result.latencyMs()).isNotNull().isGreaterThanOrEqualTo(0L);
  }

  private static DecideService pipeline(DecideLayer classifier, DecideLayer llmFallback) {
    return new DecideService(
        new CatalogueService(new InMemoryRouteStore().seedDemo()),
        new BusinessEvents(new SimpleMeterRegistry()),
        new RulesLayer(demoRules()),
        classifier,
        llmFallback,
        DecideService.LAYER_TWO_BUDGET_MS,
        false,
        LlmFallbackPool.create(),
        DecideService.LAYER_THREE_TIMEOUT_MS);
  }

  private static IntentRuleStore demoRules() {
    return new InMemoryIntentRuleStore().seedDemo();
  }

  private static DecideLayer counting(AtomicInteger calls) {
    return (request, eligible) -> {
      calls.incrementAndGet();
      return Optional.empty();
    };
  }

  private static DecideRequest chat(String message, Map<String, Object> claims) {
    return new DecideRequest("chat", "web", "sess-88", message, null, claims);
  }

  private static Map<String, Object> jane() {
    return Map.of("sub", "jane", "emts", Map.of("support:case", true));
  }
}
