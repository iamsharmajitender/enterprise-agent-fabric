package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedChatHiddenRoutesSqlTest {

  @Test
  void flywayBaselineKeepsJobRoutesOffChat() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    for (String id :
        new String[] {
          "email_summarize", "contract_investigation", "msa_risk_review", "kyc_onboarding"
        }) {
      assertThat(seed).contains("'" + id + "'");
    }
    assertThat(count(seed, "FALSE")).isGreaterThanOrEqualTo(4);
    assertThat(seed).contains("'summarize_email'");
    assertThat(seed).contains("'kyc_onboard'");
  }

  @Test
  void flywayBaselineIncludesGuidedContractReview() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("'contract_review'");
    assertThat(seed).contains("allowlist");
    assertThat(seed).contains("max_tool_calls");
    assertThat(seed).contains("autonomy_mode");
  }

  @Test
  void flywayBaselineIncludesKycRetrieval() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("'kyc_onboarding'");
    assertThat(seed).contains("'tool'");
    assertThat(seed).contains("sanctions-lists");
    assertThat(seed).contains("kyc-policy");
  }

  @Test
  void flywayBaselineIncludesPolicyQaPrefetchCorpora() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("'agent-policy-qa'");
    assertThat(seed).contains("policy-engine");
    assertThat(seed).contains("product-faq");
  }

  @Test
  void flywayBaselineIncludesWorkflowTableAndKycStages() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("CREATE TABLE dataplane.workflows");
    assertThat(seed).contains("'kyc_onboarding'");
    assertThat(seed).contains("doc_intake");
    assertThat(seed).contains("human_gate");
    assertThat(seed).contains("'msa_risk_review'");
  }

  @Test
  void flywayBaselineIncludesCorporaCatalog() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("CREATE TABLE dataplane.corpora");
    assertThat(seed).contains("'policy-engine'");
    assertThat(seed).contains("'clause-index'");
    assertThat(seed).contains("'legal-playbook'");
    assertThat(seed).contains("'product-faq'");
    assertThat(seed).contains("'research-index'");
    assertThat(seed).contains("http://agent-mocks:3010/v1/search/assistant");
    assertThat(seed).contains("http://agent-mocks:3010/v1/search/legal");
    assertThat(seed).contains("http://agent-mocks:3010/corpora/research-index/search");
  }

  @Test
  void flywayBaselineAssignsAutonomyMode() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("autonomy_mode");
    assertThat(seed).contains("'fee_explain'");
    assertThat(seed).contains("'contract_investigation'");
    assertThat(seed).contains("'msa_risk_review'");
    assertThat(seed).contains("'kyc_onboarding'");
  }

  private static int count(String haystack, String needle) {
    int n = 0;
    for (int from = 0; (from = haystack.indexOf(needle, from)) >= 0; from += needle.length()) {
      n++;
    }
    return n;
  }

  private static String read(String path) throws Exception {
    try (var in = SeedChatHiddenRoutesSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }
}
