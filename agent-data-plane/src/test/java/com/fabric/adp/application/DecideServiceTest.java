package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.ForbiddenException;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class DecideServiceTest {

  private DecideService decide;

  @BeforeEach
  void setUp() {
    decide = new DecideService(new CatalogueService(new InMemoryRouteStore().seedDemo()));
  }

  @Test
  void feeUtteranceRoutesToFeeExplain() {
    DecideResult result = decide.decide(chat("Why was I charged $42?", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("fee_explain");
    assertThat(result.routeVersion()).isEqualTo("2026.08.1");
  }

  @Test
  void emptyEligibleAbstains() {
    DecideResult result =
        decide.decide(
            new DecideRequest("chat", "sms", "s", "Why was I charged $42?", null, jane()), "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
  }

  @Test
  void closeKeywordMatchClarifies() {
    DecideResult result = decide.decide(chat("hello", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("clarify");
    assertThat(result.candidates()).hasSize(2);
  }

  @Test
  void explicitRouteIdBindsWithoutKeywords() {
    DecideResult result =
        decide.decide(
            new DecideRequest("jobs", "web", "job:1", null, "fee_explain", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("fee_explain");
    assertThat(result.confidence()).isEqualTo(1.0);
  }

  @Test
  void arCallerIsForbidden() {
    org.assertj.core.api.Assertions.assertThatThrownBy(
            () -> decide.decide(chat("Why was I charged $42?", jane()), "ar"))
        .isInstanceOf(ForbiddenException.class);
  }

  private static DecideRequest chat(String message, Map<String, Object> claims) {
    return new DecideRequest("chat", "web", "sess-88", message, null, claims);
  }

  private static Map<String, Object> jane() {
    return Map.of("sub", "jane", "emts", Map.of("accounts:read", true));
  }
}
