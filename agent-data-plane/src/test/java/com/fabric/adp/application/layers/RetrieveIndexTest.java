package com.fabric.adp.application.layers;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;

class RetrieveIndexTest {

  private final RetrieveIndex index = RetrieveIndex.loadDefault();

  @Test
  void hiIsNotInsideThis() {
    assertThat(RetrieveIndex.tokens("Start KYC onboarding for this applicant")).doesNotContain("hi");
    assertThat(RetrieveIndex.tokens("hi")).containsExactly("hi");
  }

  @Test
  void dollarAmountTokenizesAsDigits() {
    assertThat(RetrieveIndex.tokens("Why was I charged $42?")).contains("charged", "42");
  }

  @Test
  void exactFeeUtteranceScoresOneAgainstFeeExplain() {
    assertThat(index.bestScore("Why was I charged $42?", "fee_explain")).isEqualTo(1.0);
    assertThat(index.bestScore("Why was I charged $42?", "card_freeze"))
        .isLessThan(RetrieveIndex.OOD_THRESHOLD);
  }

  @Test
  void freezeUtteranceDoesNotScoreFee() {
    assertThat(index.bestScore("Please freeze this card", "card_freeze")).isEqualTo(1.0);
    assertThat(index.bestScore("Please freeze this card", "fee_explain"))
        .isLessThan(RetrieveIndex.OOD_THRESHOLD);
  }

  @Test
  void emptyMessageIsOod() {
    assertThat(index.bestScore("", "fee_explain")).isZero();
    assertThat(index.bestScore(null, "fee_explain")).isZero();
  }

  @Test
  void cosineOfIdenticalSetsIsOne() {
    Set<String> tokens = Set.of("charged", "42");
    assertThat(RetrieveIndex.cosine(tokens, tokens)).isEqualTo(1.0);
  }

  @Test
  void unknownRouteScoresZero() {
    assertThat(index.bestScore("Why was I charged $42?", "not_a_route")).isZero();
  }

  @Test
  void loadDefaultIndexesUtterancesNotKeywordLists() {
    assertThat(new RetrieveIndex(List.of()).bestScore("fee charged 42 monthly", "fee_explain"))
        .isZero();
    assertThat(index.bestScore("Why was I charged $42?", "fee_explain")).isEqualTo(1.0);
  }
}
