package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedChatHiddenRoutesSqlTest {

  @Test
  void flywaySeedAddsJobRoutesThatAreNotChatVisible() throws Exception {
    String seed = read("/db/migration/V13__seed_chat_hidden_job_routes.sql");
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
  void flywaySeedAddsGuidedContractReview() throws Exception {
    String seed = read("/db/migration/V19__seed_contract_review.sql");
    assertThat(seed).contains("'contract_review'");
    assertThat(seed).contains("'contract_review_v3'");
    assertThat(seed).contains("'contract_review_staged_v3'");
    assertThat(seed).contains("allowlist");
    assertThat(seed).contains("max_tool_calls");
    assertThat(seed).contains("keywords, pattern");
    assertThat(seed).contains("  3\n);");
  }

  @Test
  void flywaySeedAddsKycRetrieval() throws Exception {
    String seed = read("/db/migration/V14__kyc_onboarding_retrieval.sql");
    assertThat(seed).contains("'kyc_onboarding'");
    assertThat(seed).contains("'tool'");
    assertThat(seed).contains("sanctions-lists");
    assertThat(seed).contains("kyc-policy");
  }

  @Test
  void flywaySeedAddsPolicyQaPrefetchCorpora() throws Exception {
    String seed = read("/db/migration/V15__policy_qa_prefetch_scope.sql");
    assertThat(seed).contains("'agent-policy-qa-v1'");
    assertThat(seed).contains("policy-engine");
    assertThat(seed).contains("product-faq");
  }

  @Test
  void flywaySeedAddsWorkflowTableAndKycStages() throws Exception {
    String seed = read("/db/migration/V16__workflows.sql");
    assertThat(seed).contains("CREATE TABLE dataplane.workflows");
    assertThat(seed).contains("'kyc_onboarding_v2'");
    assertThat(seed).contains("doc_intake");
    assertThat(seed).contains("human_gate");
    assertThat(seed).contains("'msa_risk_review_v1'");
  }

  @Test
  void flywaySeedAddsCorporaCatalog() throws Exception {
    String seed = read("/db/migration/V18__corpora.sql");
    assertThat(seed).contains("CREATE TABLE dataplane.corpora");
    assertThat(seed).contains("'policy-engine'");
    assertThat(seed).contains("'clause-index'");
    assertThat(seed).contains("'legal-playbook'");
    assertThat(seed).contains("'product-faq'");
    assertThat(seed).contains("'research-index'");
    assertThat(seed).contains("https://retrieve.internal/v1/search");
  }

  @Test
  void flywaySeedAssignsAutonomyPatterns() throws Exception {
    String seed = read("/db/migration/V17__route_pattern.sql");
    assertThat(seed).contains("ADD COLUMN pattern");
    assertThat(seed).contains("pattern BETWEEN 0 AND 3");
    assertThat(seed).contains("'fee_explain'");
    assertThat(seed).contains("'contract_investigation'");
    assertThat(seed).contains("'agent-research-v0'");
    assertThat(seed).contains("'agent-payments-v2'");
    assertThat(seed).contains("'msa_risk_review'");
    assertThat(seed).contains("'kyc_onboarding'");
  }

  @Test
  void flywayRenamesPatternToAutonomyModeAndReclassifiesFeeExplain() throws Exception {
    String seed = read("/db/migration/V20__rename_pattern_to_autonomy_mode.sql");
    assertThat(seed).contains("RENAME COLUMN pattern TO autonomy_mode");
    assertThat(seed).contains("routes_autonomy_mode_chk");
    assertThat(seed).contains("'fee_explain'");
    assertThat(seed).contains("pattern = 0");
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
