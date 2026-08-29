package com.fabric.adp.domain;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import org.junit.jupiter.api.Test;

class PromptPackTest {

  private final PromptPack pack =
      new PromptPack(
          "msa_risk_review_v1",
          "2026.08.1",
          "You are counsel's MSA risk-review worker.",
          "published",
          "legal-agents",
          List.of(
              new PromptRoleTemplate(
                  "query_formulation", "plan", "Write the search query for this stage's corpus only."),
              new PromptRoleTemplate(
                  "synthesis", "synthesize", "Draft the counsel memo from validated stage outputs only.")));

  @Test
  void selectsTemplateByLlmRole() {
    assertThat(pack.role("query_formulation"))
        .map(PromptRoleTemplate::taskType)
        .contains("plan");
    assertThat(pack.role("synthesis")).map(PromptRoleTemplate::taskType).contains("synthesize");
  }

  @Test
  void noneOrMissingRoleSkipsTheStore() {
    assertThat(pack.role("none")).isEmpty();
    assertThat(pack.role(null)).isEmpty();
    assertThat(pack.role("clause_search")).isEmpty();
  }
}
