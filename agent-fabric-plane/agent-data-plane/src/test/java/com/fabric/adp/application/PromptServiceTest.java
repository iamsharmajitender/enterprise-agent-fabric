package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.domain.PromptPack;
import com.fabric.adp.domain.NotFoundException;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PromptServiceTest {

  private final PromptService prompts = new PromptService(new InMemoryPromptStore().seedDemo());

  @Test
  void shopassistPackIsHostOnly() {
    PromptPack pack = prompts.get("shopassist_case", "2026.08.1");
    assertThat(pack.host()).contains("ShopAssist front-line support");
    assertThat(pack.owner()).isEqualTo("shopassist");
    assertThat(pack.roles()).isEmpty();
  }

  @Test
  void listPublishedSeedPrompts() {
    assertThat(prompts.listAll()).extracting(PromptPack::promptId).containsExactly("shopassist_case");
    assertThat(prompts.listPublished()).extracting(PromptPack::promptId).containsExactly("shopassist_case");
    assertThat(prompts.published("shopassist_case").promptVersion()).isEqualTo("2026.08.1");
  }

  @Test
  void missingPinIsNotFound() {
    assertThatThrownBy(() -> prompts.get("shopassist_case", "1999.01.1"))
        .isInstanceOf(NotFoundException.class)
        .hasMessageContaining("shopassist_case@1999.01.1");
  }
}
