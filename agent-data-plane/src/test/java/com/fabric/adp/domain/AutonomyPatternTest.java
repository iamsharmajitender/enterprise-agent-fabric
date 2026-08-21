package com.fabric.adp.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class AutonomyPatternTest {

  @Test
  void codesAreTheClosedSet() {
    assertThat(AutonomyPattern.fromCode(0)).isEqualTo(AutonomyPattern.SINGLE_INFERENCE);
    assertThat(AutonomyPattern.fromCode(1)).isEqualTo(AutonomyPattern.AUTONOMOUS);
    assertThat(AutonomyPattern.fromCode(2)).isEqualTo(AutonomyPattern.DETERMINISTIC);
    assertThat(AutonomyPattern.fromCode(3)).isEqualTo(AutonomyPattern.GUIDED);
    assertThat(AutonomyPattern.SINGLE_INFERENCE.code()).isEqualTo(0);
  }

  @Test
  void unknownCodeIsRejected() {
    assertThatThrownBy(() -> AutonomyPattern.fromCode(4))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("4");
  }
}
