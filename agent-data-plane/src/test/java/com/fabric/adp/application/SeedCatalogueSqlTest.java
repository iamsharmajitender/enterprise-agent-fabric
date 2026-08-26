package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedCatalogueSqlTest {

  private static final String[] ROUTES = {
    "agent-chat",
    "email_summarize",
    "chat_session",
    "agent-policy-qa",
    "policy_chat",
    "search_only",
    "research_assistant",
    "fraud_one_tool",
    "fraud_casefile",
    "fee_explain",
    "contract_investigation",
    "llm_pipeline",
    "policy_memo",
    "account_notify",
    "card_freeze",
    "dispute_intake",
    "purchase_refund",
    "pack_then_notify",
    "pack_then_freeze",
    "pack_then_review",
    "clause_lookup",
    "template_retrieve",
    "msa_risk_review",
    "kyc_onboarding",
    "claims_adjudicate",
    "ticket_triage",
    "product_explain",
    "narrow_review",
    "contract_review",
    "due_diligence",
    "fraud_investigate",
    "ops_start_kyc"
  };

  @Test
  void flywayBaselineContainsEveryCatalogueRoute() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    for (String id : ROUTES) {
      assertThat(seed).contains("'" + id + "'");
    }
    assertThat(seed).contains("autonomy_mode");
    assertThat(seed).contains("deterministic_prefetch");
    assertThat(seed).doesNotContain("No prompt");
    assertThat(seed).contains("host plus synthesis");
  }

  @Test
  void flywayIntentRulesSeedSlashCommands() throws Exception {
    String seed = read("/db/migration/V2__intent_rules.sql");
    assertThat(seed).contains("dataplane.intent_rules");
    assertThat(seed).contains("'/hr'");
    assertThat(seed).contains("'agent-chat'");
    assertThat(seed).contains("'talk to a human'");
    assertThat(seed).contains("'/freeze'");
    assertThat(seed).contains("'card_freeze'");
  }

  private static String read(String path) throws Exception {
    try (var in = SeedCatalogueSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }
}
