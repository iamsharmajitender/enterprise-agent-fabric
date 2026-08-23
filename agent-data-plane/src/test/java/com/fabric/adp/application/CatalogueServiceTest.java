package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.domain.AutonomyPattern;
import com.fabric.adp.domain.MemoryProfile;
import com.fabric.adp.domain.ModelProfile;
import com.fabric.adp.domain.Retrieval;
import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;

class CatalogueServiceTest {

  private final CatalogueService catalogue =
      new CatalogueService(new InMemoryRouteStore().seedDemo());

  @Test
  void listAllIsTheTeachingCatalogue() {
    assertThat(catalogue.list()).extracting(RouteRow::routeId)
        .contains("fee_explain", "agent-chat", "agent-policy-qa", "contract_review")
        .doesNotContain("agent-research-v0", "agent-payments-v2");
    assertThat(catalogue.listAll()).hasSize(31);
  }

  @Test
  void janeSeesFeeAndOpenChatNotLegalJobs() {
    var eligible = catalogue.eligible("web", Set.of("accounts:read"));
    assertThat(eligible).extracting(RouteRow::routeId)
        .contains("fee_explain", "agent-chat", "chat_session", "search_only")
        .doesNotContain("kyc_onboarding", "contract_review", "email_summarize");
  }

  @Test
  void chatHiddenJobRoutesStayOffEligible() {
    assertThat(catalogue.list())
        .filteredOn(row -> !row.chatVisible())
        .extracting(RouteRow::routeId)
        .contains(
            "email_summarize",
            "contract_investigation",
            "msa_risk_review",
            "kyc_onboarding",
            "contract_review",
            "fraud_investigate",
            "ops_start_kyc");
    assertThat(catalogue.eligible("web", Set.of("accounts:read", "legal:read", "kyc:onboard", "fraud:read")))
        .extracting(RouteRow::routeId)
        .doesNotContain(
            "email_summarize",
            "contract_investigation",
            "msa_risk_review",
            "kyc_onboarding",
            "contract_review",
            "fraud_investigate",
            "ops_start_kyc");
  }

  @Test
  void pinnedFeeExplainIsPatternOneRetrieveTool() {
    RouteRow row = catalogue.get("fee_explain", "2026.08.1");
    assertThat(row.manifest().manifestId()).isEqualTo("fee_explain");
    assertThat(row.autonomyMode()).isEqualTo(AutonomyPattern.AUTONOMOUS);
    assertThat(row.activationTarget()).isEqualTo("http://agent-runtime:3008/v1/runs");
    assertThat(row.promptId()).isEqualTo("fee_explain");
    assertThat(row.modelProfile()).isEqualTo(ModelProfile.REASONING_STANDARD);
    assertThat(row.retrieval()).isEqualTo(new Retrieval("tool", List.of("accounts")));
    assertThat(row.memoryProfile()).isEqualTo(
        new MemoryProfile(
            "session", "session", "checkpoint", "retrieve_only", 24,
            List.of("tenant", "user", "session")));
    assertThat(catalogue.get("agent-chat", "2026.08.1").modelProfile())
        .isEqualTo(ModelProfile.LIGHTWEIGHT_CHAT);
  }

  @Test
  void kycOnboardingPinsWorkflowAndPrompt() {
    assertThat(catalogue.get("kyc_onboarding", "2026.08.1").retrieval())
        .isEqualTo(new Retrieval("tool", List.of("sanctions-lists", "kyc-policy")));
    assertThat(catalogue.get("kyc_onboarding", "2026.08.1").workflowId())
        .isEqualTo("kyc_onboarding");
    assertThat(catalogue.get("kyc_onboarding", "2026.08.1").promptId())
        .isEqualTo("kyc_onboarding");
  }

  @Test
  void policyQaPrefetchesPolicyEngineAndProductFaq() {
    assertThat(catalogue.get("agent-policy-qa", "2026.08.1").retrieval())
        .isEqualTo(new Retrieval("deterministic_prefetch", List.of("policy-engine", "product-faq")));
  }

  @Test
  void chatAndEmailHaveNoRetrieval() {
    assertThat(catalogue.get("agent-chat", "2026.08.1").retrieval()).isNull();
    assertThat(catalogue.get("email_summarize", "2026.08.1").retrieval()).isNull();
  }

  @Test
  void clauseSearchIsSharedAcrossLegalRetrieveRoutes() {
    assertThat(catalogue.list())
        .filteredOn(
            row ->
                row.manifest() != null
                    && row.manifest().tools().stream()
                        .anyMatch(tool -> "clause_search".equals(tool.capabilityId())))
        .extracting(RouteRow::routeId)
        .contains("contract_investigation", "msa_risk_review", "contract_review", "due_diligence");
  }

  @Test
  void feeExplainHasASingleActiveVersion() {
    assertThat(catalogue.versions("fee_explain")).extracting(RouteRow::routeVersion)
        .containsExactly("2026.08.1");
  }

  @Test
  void eachRouteGetsAnAutonomyPattern() {
    Map<String, AutonomyPattern> expected =
        catalogue.listAll().stream()
            .collect(Collectors.toMap(RouteRow::routeId, RouteRow::autonomyMode));
    assertThat(expected).hasSize(31);
    assertThat(expected.get("agent-chat")).isEqualTo(AutonomyPattern.SINGLE_INFERENCE);
    assertThat(expected.get("fee_explain")).isEqualTo(AutonomyPattern.AUTONOMOUS);
    assertThat(expected.get("kyc_onboarding")).isEqualTo(AutonomyPattern.DETERMINISTIC);
    assertThat(expected.get("due_diligence")).isEqualTo(AutonomyPattern.GUIDED);
    expected.forEach(
        (routeId, pattern) ->
            assertThat(catalogue.get(routeId, "2026.08.1").autonomyMode()).isEqualTo(pattern));
  }
}
