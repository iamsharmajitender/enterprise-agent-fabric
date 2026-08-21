package com.fabric.registry.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedCapabilitiesSqlTest {

  @Test
  void flywaySeedCoversEveryManifestToolCapability() throws Exception {
    String seed = read("/db/migration/V3__seed_capabilities.sql")
        + read("/db/migration/V4__seed_tool_capabilities.sql")
        + read("/db/migration/V7__seed_job_route_capabilities.sql");
    for (String id :
        new String[] {
          "account_fee_lookup",
          "list_accounts",
          "list_transactions",
          "lookup_beneficiary",
          "validate_payment",
          "initiate_wire",
          "escalate_to_human",
          "search_transactions",
          "ocr_extract",
          "start_contract_review",
          "clause_search",
          "policy_search",
          "risk_engine",
          "draft_memo",
          "doc_intake",
          "id_verify",
          "sanctions_api",
          "kyc_risk_engine",
          "account_activate"
        }) {
      assertThat(seed).contains("'" + id + "'");
    }
  }

  @Test
  void flywaySeedIncludesPublishedCapabilitiesWithNoManifest() throws Exception {
    String unused = read("/db/migration/V6__seed_unused_capabilities.sql");
    for (String id :
        new String[] {"kyc_document_verify", "aml_watchlist_screen", "credit_limit_lookup"}) {
      assertThat(unused).contains("'" + id + "'");
    }
    assertThat(unused).contains("'published'");
    assertThat(unused).doesNotContain("capability_id");
  }

  private static String read(String path) throws Exception {
    try (var in = SeedCapabilitiesSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }
}
