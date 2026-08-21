package com.fabric.adp.adapters.in.http;

import static org.hamcrest.Matchers.nullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fabric.adp.application.CatalogueService;
import com.fabric.adp.application.CorpusService;
import com.fabric.adp.application.DecideService;
import com.fabric.adp.application.InMemoryCorpusStore;
import com.fabric.adp.application.InMemoryManifestStore;
import com.fabric.adp.application.InMemoryPromptStore;
import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.application.InMemoryWorkflowStore;
import com.fabric.adp.application.ManifestService;
import com.fabric.adp.application.PromptService;
import com.fabric.adp.application.WorkflowService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(
    controllers = {
      CatalogController.class,
      ManifestController.class,
      PromptController.class,
      CorpusController.class,
      WorkflowController.class,
      DecideController.class,
      ApiExceptionHandler.class
    })
@Import({WorkloadAuthFilter.class, CatalogAndDecideControllerTest.MemConfig.class})
class CatalogAndDecideControllerTest {

  @Autowired private MockMvc mvc;

  @Test
  void listsRoutesAndGetsFeeExplain() throws Exception {
    mvc.perform(
            get("/v1/catalog/routes")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.route_table_version").doesNotExist())
        .andExpect(jsonPath("$.routes[?(@.route_id=='fee_explain')]").exists());

    mvc.perform(
            get("/v1/catalog/routes/fee_explain")
                .queryParam("route_version", "2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.tool_manifest").value("fee_explain"))
        .andExpect(jsonPath("$.route_version").value("2026.08.1"))
        .andExpect(jsonPath("$.active").value(true))
        .andExpect(jsonPath("$.model_profile").value("reasoning-standard"))
        .andExpect(jsonPath("$.retrieval.mode").value("tool"))
        .andExpect(jsonPath("$.retrieval.scope[0]").value("accounts"))
        .andExpect(jsonPath("$.memory_profile.conversation").value("session"))
        .andExpect(jsonPath("$.memory_profile.ttl_hours").value(24))
        .andExpect(jsonPath("$.manifest.manifest_id").value("fee_explain"))
        .andExpect(jsonPath("$.manifest.tools[0].name").value("account_fee_lookup"))
        .andExpect(jsonPath("$.manifest.tools[0].capability_id").value("account_fee_lookup"))
        .andExpect(jsonPath("$.manifest.tools[0].capability_version").value("1.0.0"))
        .andExpect(jsonPath("$.prompt_id").value("fee_explain"))
        .andExpect(jsonPath("$.autonomy_mode").value(1));
  }

  @Test
  void policyQaUsesDeterministicPrefetchAcrossTwoCorpora() throws Exception {
    mvc.perform(
            get("/v1/catalog/routes/agent-policy-qa")
                .queryParam("route_version", "2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.retrieval.mode").value("deterministic_prefetch"))
        .andExpect(jsonPath("$.retrieval.scope[0]").value("policy-engine"))
        .andExpect(jsonPath("$.retrieval.scope[1]").value("product-faq"));
  }

  @Test
  void chatRouteOmitsRetrievalWhenThereIsNoKnowledgePath() throws Exception {
    mvc.perform(
            get("/v1/catalog/routes/agent-chat")
                .queryParam("route_version", "2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.retrieval").value(nullValue()))
        .andExpect(jsonPath("$.autonomy_mode").value(0));
  }

  @Test
  void includeAllSurfacesTeachingRoutesAndDraftCorpus() throws Exception {
    mvc.perform(
            get("/v1/catalog/routes")
                .queryParam("include", "all")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.routes[?(@.route_id=='due_diligence')]").isNotEmpty())
        .andExpect(jsonPath("$.routes[?(@.route_id=='agent-research-v0')]").isEmpty());

    mvc.perform(
            get("/v1/catalog/prompts")
                .queryParam("include", "all")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.prompts[?(@.prompt_id=='due_diligence')]").isNotEmpty())
        .andExpect(jsonPath("$.prompts[?(@.prompt_id=='fee_explain')]").isNotEmpty());

    mvc.perform(
            get("/v1/catalog/manifests")
                .queryParam("include", "all")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.manifests[?(@.manifest_id=='due_diligence')]").isNotEmpty())
        .andExpect(jsonPath("$.manifests[?(@.manifest_id=='fax_lookup')]").isEmpty());

    mvc.perform(
            get("/v1/catalog/corpora")
                .queryParam("include", "all")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.corpora[?(@.corpus_id=='research-index')]").isNotEmpty())
        .andExpect(jsonPath("$.corpora[?(@.status=='draft')].corpus_id").value("research-index"));
  }

  @Test
  void listsPublishedPromptsAndManifests() throws Exception {
    mvc.perform(
            get("/v1/catalog/prompts")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.prompts[?(@.prompt_id=='fee_explain')]").exists())
        .andExpect(jsonPath("$.prompts[?(@.prompt_id=='due_diligence')]").exists());

    mvc.perform(
            get("/v1/catalog/prompts/fee_explain/versions")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.prompt_id").value("fee_explain"))
        .andExpect(jsonPath("$.versions[0].prompt_version").value("2026.08.1"));

    mvc.perform(
            get("/v1/catalog/manifests")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.manifests[?(@.manifest_id=='fee_explain')]").exists());

    mvc.perform(
            get("/v1/catalog/manifests/fee_explain")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.manifest_id").value("fee_explain"))
        .andExpect(jsonPath("$.manifest_version").value("2026.08.1"));

    mvc.perform(
            get("/v1/catalog/manifests/fee_explain/versions")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.manifest_id").value("fee_explain"))
        .andExpect(jsonPath("$.versions[0].manifest_version").value("2026.08.1"));

    mvc.perform(
            get("/v1/catalog/corpora")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.corpora[?(@.corpus_id=='policy-engine')]").exists())
        .andExpect(jsonPath("$.corpora[?(@.corpus_id=='research-index')]").doesNotExist());
  }

  @Test
  void listsKycWorkflowWithFixedStages() throws Exception {
    mvc.perform(
            get("/v1/catalog/workflows/kyc_onboarding")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.workflow_id").value("kyc_onboarding"))
        .andExpect(jsonPath("$.workflow_version").value("2026.08.1"))
        .andExpect(jsonPath("$.status").value("published"))
        .andExpect(jsonPath("$.stages[0].id").value("collect_docs"))
        .andExpect(jsonPath("$.stages[0].tool").value("doc_intake"))
        .andExpect(jsonPath("$.stages[3].branch.high").value("manual_review"))
        .andExpect(jsonPath("$.stages[4].type").value("human_gate"))
        .andExpect(jsonPath("$.stages[5].requires_approval").value(true));
  }

  @Test
  void listsGuidedContractReviewWorkflow() throws Exception {
    mvc.perform(
            get("/v1/catalog/workflows/contract_review")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.workflow_id").value("contract_review"))
        .andExpect(jsonPath("$.stages[0].id").value("extract"))
        .andExpect(jsonPath("$.stages[0].tool").value("ocr_extract"))
        .andExpect(jsonPath("$.stages[1].id").value("analyse"))
        .andExpect(jsonPath("$.stages[1].allowlist[0]").value("clause_search"))
        .andExpect(jsonPath("$.stages[1].allowlist[2]").value("risk_engine"))
        .andExpect(jsonPath("$.stages[1].max_tool_calls").value(6))
        .andExpect(jsonPath("$.stages[2].tool").value("draft_memo"));
  }

  @Test
  void contractReviewRouteIsPatternThree() throws Exception {
    mvc.perform(
            get("/v1/catalog/routes/contract_review")
                .queryParam("route_version", "2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.autonomy_mode").value(3))
        .andExpect(jsonPath("$.workflow_id").value("contract_review"))
        .andExpect(jsonPath("$.tool_manifest").value("contract_review"))
        .andExpect(jsonPath("$.chat_visible").value(false));
  }

  @Test
  void kycRoutePinsWorkflowAndPromptIds() throws Exception {
    mvc.perform(
            get("/v1/catalog/routes/kyc_onboarding")
                .queryParam("route_version", "2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.workflow_id").value("kyc_onboarding"))
        .andExpect(jsonPath("$.prompt_id").value("kyc_onboarding"));
  }

  @Test
  void getsMsaPromptPackWithTwoRoles() throws Exception {
    mvc.perform(
            get("/v1/catalog/prompts/msa_risk_review/versions/2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.prompt_id").value("msa_risk_review"))
        .andExpect(jsonPath("$.prompt_version").value("2026.08.1"))
        .andExpect(jsonPath("$.status").value("published"))
        .andExpect(jsonPath("$.owner").value("legal-agents"))
        .andExpect(jsonPath("$.by_llm_role.query_formulation.task_type").value("plan"))
        .andExpect(jsonPath("$.by_llm_role.synthesis.task_type").value("synthesize"));
  }

  @Test
  void getsPublishedPromptPackById() throws Exception {
    mvc.perform(
            get("/v1/catalog/prompts/fee_explain")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.prompt_id").value("fee_explain"))
        .andExpect(jsonPath("$.status").value("published"));
  }

  @Test
  void getsHostOnlyPromptPack() throws Exception {
    mvc.perform(
            get("/v1/catalog/prompts/email_summarize")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.prompt_id").value("email_summarize"))
        .andExpect(jsonPath("$.by_llm_role").isEmpty())
        .andExpect(
            jsonPath("$.host")
                .value("Summarize this email for the banker. No tools. Return short bullets."));
  }

  @Test
  void getsPublishedCorpusForNarLookup() throws Exception {
    mvc.perform(
            get("/v1/catalog/corpora/policy-engine")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.corpus_id").value("policy-engine"))
        .andExpect(jsonPath("$.url").value("https://retrieve.internal/v1/search"))
        .andExpect(jsonPath("$.collection").value("policy-engine"))
        .andExpect(jsonPath("$.auth").value("workload-oauth"))
        .andExpect(jsonPath("$.owner").value("policy-ops"))
        .andExpect(jsonPath("$.status").value("published"))
        .andExpect(jsonPath("$.region").value(nullValue()))
        .andExpect(jsonPath("$.updated_at").exists());
  }

  @Test
  void twoScopeIdsResolveToTwoSeparateCorpusRows() throws Exception {
    mvc.perform(
            get("/v1/catalog/corpora/clause-index")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.corpus_id").value("clause-index"))
        .andExpect(jsonPath("$.collection").value("clause-index"));

    mvc.perform(
            get("/v1/catalog/corpora/legal-playbook")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.corpus_id").value("legal-playbook"))
        .andExpect(jsonPath("$.collection").value("legal-playbook"))
        .andExpect(jsonPath("$.url").value("https://retrieve.internal/v1/search"));
  }

  @Test
  void missingCorpusIsNotFound() throws Exception {
    mvc.perform(
            get("/v1/catalog/corpora/missing-index")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isNotFound());
  }

  @Test
  void missingPromptVersionIsNotFound() throws Exception {
    mvc.perform(
            get("/v1/catalog/prompts/msa_risk_review/versions/1999.01.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isNotFound());
  }

  @Test
  void listsFeeExplainVersionsNewestFirst() throws Exception {
    mvc.perform(
            get("/v1/catalog/routes/fee_explain/versions")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.route_id").value("fee_explain"))
        .andExpect(jsonPath("$.versions[0].route_version").value("2026.08.1"))
        .andExpect(jsonPath("$.versions.length()").value(1));
  }

  @Test
  void getsCardFreezeManifestDocument() throws Exception {
    mvc.perform(
            get("/v1/catalog/manifests/card_freeze/versions/2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.manifest_id").value("card_freeze"))
        .andExpect(jsonPath("$.tools[0].name").value("identity_check"))
        .andExpect(jsonPath("$.tools[2].name").value("freeze_card"))
        .andExpect(jsonPath("$.tools[2].risk_tier").value("high"));

    mvc.perform(
            get("/v1/catalog/routes/card_freeze")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.tool_manifest").value("card_freeze"))
        .andExpect(jsonPath("$.workflow_id").value("card_freeze"))
        .andExpect(jsonPath("$.autonomy_mode").value(2));
  }

  @Test
  void getsFraudCasefileManifest() throws Exception {
    mvc.perform(
            get("/v1/catalog/manifests/fraud_casefile/versions/2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.manifest_id").value("fraud_casefile"))
        .andExpect(jsonPath("$.tools[0].capability_id").value("ocr_extract"))
        .andExpect(jsonPath("$.tools[2].name").value("draft_memo"));
  }

  @Test
  void channelBearerIsUnauthorized() throws Exception {
    mvc.perform(get("/v1/catalog/routes")).andExpect(status().isUnauthorized());
  }

  @Test
  void decideFeeMessage() throws Exception {
    mvc.perform(
            post("/v1/intent/decide")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "afd")
                .contentType(MediaType.APPLICATION_JSON)
                .content(
                    """
                    {"ingress":"chat","channel":"web","session_id":"sess-88",
                     "message":"Why was I charged $42?","route_id":null,
                     "claims":{"sub":"jane","emts":{"accounts:read":true}}}
                    """))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.outcome").value("route"))
        .andExpect(jsonPath("$.route_id").value("fee_explain"));
  }

  @Test
  void arDecideIsForbidden() throws Exception {
    mvc.perform(
            post("/v1/intent/decide")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"ingress\":\"chat\",\"channel\":\"web\",\"message\":\"x\"}"))
        .andExpect(status().isForbidden());
  }

  @Test
  void decisionsApiDoesNotExist() throws Exception {
    mvc.perform(
            get("/v1/decisions")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isNotFound());
  }

  @TestConfiguration
  static class MemConfig {
    @Bean
    CatalogueService catalogueService() {
      return new CatalogueService(new InMemoryRouteStore().seedDemo());
    }

    @Bean
    ManifestService manifestService() {
      return new ManifestService(new InMemoryManifestStore().seedDemo());
    }

    @Bean
    PromptService promptService() {
      return new PromptService(new InMemoryPromptStore().seedDemo());
    }

    @Bean
    CorpusService corpusService() {
      return new CorpusService(new InMemoryCorpusStore().seedDemo());
    }

    @Bean
    WorkflowService workflowService() {
      return new WorkflowService(new InMemoryWorkflowStore().seedDemo());
    }

    @Bean
    DecideService decideService(CatalogueService catalogue) {
      return new DecideService(catalogue);
    }
  }
}
