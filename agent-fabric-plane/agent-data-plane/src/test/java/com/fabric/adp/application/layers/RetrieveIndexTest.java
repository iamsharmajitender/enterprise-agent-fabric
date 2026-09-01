package com.fabric.adp.application.layers;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;

class RetrieveIndexTest {

  private final RetrieveIndex index = RetrieveIndex.loadDefault();

  @Test
  void shopassistUtteranceScoresOneAgainstShopassistCase() {
    assertThat(index.bestScore("My blue jacket arrived damaged and I want a refund", "shopassist_case"))
        .isEqualTo(1.0);
  }

  @Test
  void feeExplainUtteranceScoresOneAgainstFeeExplain() {
    assertThat(index.bestScore("Why was I charged $42?", "fee_explain")).isEqualTo(1.0);
  }

  @Test
  void unrelatedUtteranceScoresBelowThreshold() {
    assertThat(index.bestScore("hello there", "shopassist_case"))
        .isLessThan(RetrieveIndex.OOD_THRESHOLD);
  }

  @Test
  void emptyMessageIsOod() {
    assertThat(index.bestScore("", "shopassist_case")).isZero();
    assertThat(index.bestScore(null, "shopassist_case")).isZero();
  }

  @Test
  void cosineOfIdenticalSetsIsOne() {
    Set<String> tokens = Set.of("damaged", "refund");
    assertThat(RetrieveIndex.cosine(tokens, tokens)).isEqualTo(1.0);
  }

  @Test
  void unknownRouteScoresZero() {
    assertThat(index.bestScore("damaged jacket refund", "not_a_route")).isZero();
  }

  @Test
  void loadDefaultIndexesUtterancesNotKeywordLists() {
    assertThat(new RetrieveIndex(List.of()).bestScore("damaged jacket refund", "shopassist_case"))
        .isZero();
    assertThat(index.bestScore("Damaged goods and duplicate charge on ORD-77819", "shopassist_case"))
        .isEqualTo(1.0);
  }
}
