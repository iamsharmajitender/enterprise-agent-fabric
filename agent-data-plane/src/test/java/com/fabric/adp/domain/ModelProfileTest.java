package com.fabric.adp.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class ModelProfileTest {

  @Test
  void wireIdsAreTheClosedSet() {
    assertThat(ModelProfile.fromId("reasoning-standard")).isEqualTo(ModelProfile.REASONING_STANDARD);
    assertThat(ModelProfile.fromId("fast-chat")).isEqualTo(ModelProfile.FAST_CHAT);
    assertThat(ModelProfile.fromId("lightweight-chat")).isEqualTo(ModelProfile.LIGHTWEIGHT_CHAT);
    assertThat(ModelProfile.REASONING_STANDARD.id()).isEqualTo("reasoning-standard");
  }

  @Test
  void unknownIdIsRejected() {
    assertThatThrownBy(() -> ModelProfile.fromId("gpt-4o"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("gpt-4o");
  }
}
