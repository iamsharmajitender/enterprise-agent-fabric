package com.fabric.registry.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedCapabilitiesSqlTest {

  @Test
  void flywayBaselineCoversEveryManifestToolCapability() throws Exception {
    String seed = read("/db/migration/V1__registry.sql");
    for (String id :
        new String[] {
          "account_fee_lookup",
          "ocr_extract",
          "start_contract_review",
          "start_kyc_onboarding",
          "clause_search",
          "policy_search",
          "risk_engine",
          "draft_memo",
          "doc_intake",
          "id_verify",
          "sanctions_api",
          "kyc_risk_engine",
          "account_activate",
          "extract_fields",
          "match_purchase",
          "refund_eligibility",
          "post_refund",
          "refund_confirm"
        }) {
      assertThat(seed).contains("'" + id + "'");
    }
    assertThat(seed).contains("'agent'");
    assertThat(seed).doesNotContain("'agent_start'");
    assertThat(seed).contains("\"missing_information\"");
    assertThat(seed).contains("human_review_required");
  }

  @Test
  void flywayBaselineIncludesPublishedCapabilitiesWithNoManifest() throws Exception {
    String unused = read("/db/migration/V1__registry.sql");
    for (String id :
        new String[] {"kyc_document_verify", "aml_watchlist_screen", "credit_limit_lookup"}) {
      assertThat(unused).contains("'" + id + "'");
    }
    assertThat(unused).contains("'published'");
  }

  private static String read(String path) throws Exception {
    try (var in = SeedCapabilitiesSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }
}
