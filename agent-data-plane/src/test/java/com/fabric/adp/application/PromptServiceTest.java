package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fabric.adp.domain.NotFoundException;
import com.fabric.adp.domain.PromptPack;
import com.fabric.adp.domain.PromptRoleTemplate;
import org.junit.jupiter.api.Test;

class PromptServiceTest {

  private final PromptService prompts = new PromptService(new InMemoryPromptStore().seedDemo());

  @Test
  void msaPackHasTwoRoleTemplates() {
    PromptPack pack = prompts.get("msa_risk_review", "2026.08.1");
    assertThat(pack.host()).startsWith("You are counsel's MSA risk-review worker.");
    assertThat(pack.status()).isEqualTo("published");
    assertThat(pack.owner()).isEqualTo("legal-agents");
    assertThat(pack.roles())
        .extracting(PromptRoleTemplate::llmRole)
        .containsExactly("query_formulation", "synthesis");
    assertThat(pack.role("query_formulation").orElseThrow().taskType()).isEqualTo("plan");
    assertThat(pack.role("synthesis").orElseThrow().taskType()).isEqualTo("synthesize");
  }

  @Test
  void patternZeroChatIsHostOnly() {
    PromptPack pack = prompts.get("email_summarize", "2026.08.1");
    assertThat(pack.host()).isEqualTo("Summarize this email for the banker. No tools. Return short bullets.");
    assertThat(pack.owner()).isEqualTo("assistant-platform");
    assertThat(pack.roles()).isEmpty();
  }

  @Test
  void publishedLookupUsesStatusNotLatest() {
    PromptPack pack = prompts.published("msa_risk_review");
    assertThat(pack.promptVersion()).isEqualTo("2026.08.1");
    assertThat(pack.status()).isEqualTo("published");
  }

  @Test
  void listPublishedSeedPrompts() {
    assertThat(prompts.listAll())
        .extracting(PromptPack::promptId)
        .contains("fee_explain", "email_summarize", "due_diligence")
        .doesNotContain("research");
    assertThat(prompts.listPublished())
        .extracting(PromptPack::promptId)
        .contains("fee_explain", "email_summarize", "due_diligence");
    assertThat(prompts.published("fee_explain").promptVersion()).isEqualTo("2026.08.1");
  }

  @Test
  void missingPinIsNotFound() {
    assertThatThrownBy(() -> prompts.get("msa_risk_review", "1999.01.1"))
        .isInstanceOf(NotFoundException.class)
        .hasMessageContaining("msa_risk_review@1999.01.1");
  }
}
