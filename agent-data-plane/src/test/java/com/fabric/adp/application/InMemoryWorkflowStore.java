package com.fabric.adp.application;

import com.fabric.adp.adapters.out.jdbc.WorkflowMapper;
import com.fabric.adp.domain.Workflow;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class InMemoryWorkflowStore implements WorkflowStore {

  private static final WorkflowMapper MAPPER = new WorkflowMapper(new ObjectMapper());

  private final Map<String, Workflow> rows = new LinkedHashMap<>();

  public InMemoryWorkflowStore seedDemo() {
    put(parse("llm_pipeline", "2026.08.1", "Fixed LLM stages, no tools",
        """
        [{"id":"extract","llm_role":"classify"},{"id":"rewrite","llm_role":"synthesis"},{"id":"format","llm_role":"synthesis"}]
        """));
    put(parse("policy_memo", "2026.08.1", "Prefetch then generate, no tools",
        """
        [{"id":"prefetch","llm_role":"none"},{"id":"generate","llm_role":"synthesis"}]
        """));
    put(parse("account_notify", "2026.08.1", "One-tool notify",
        """
        [{"id":"notify","tool":"notify_customer","llm_role":"none"}]
        """));
    put(parse("card_freeze", "2026.08.1", "Multi-tool freeze write path",
        """
        [{"id":"identity","tool":"identity_check","llm_role":"none"},
         {"id":"limits","tool":"limit_check","llm_role":"none"},
         {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true}]
        """));
    put(parse("dispute_intake", "2026.08.1", "Multi-tool dispute chain",
        """
        [{"id":"intake","tool":"doc_intake","llm_role":"none"},
         {"id":"open","tool":"case_open","llm_role":"none"},
         {"id":"summarize","tool":"packet_summarize","llm_role":"synthesis"}]
        """));
    put(parse("pack_then_notify", "2026.08.1", "Prefetch then one notify tool",
        """
        [{"id":"prefetch","llm_role":"none"},{"id":"notify","tool":"notify_customer","llm_role":"none"}]
        """));
    put(parse("pack_then_freeze", "2026.08.1", "Prefetch then freeze tools",
        """
        [{"id":"prefetch","llm_role":"none"},
         {"id":"identity","tool":"identity_check","llm_role":"none"},
         {"id":"limits","tool":"limit_check","llm_role":"none"},
         {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true}]
        """));
    put(parse("pack_then_review", "2026.08.1", "Prefetch playbook then tools then memo",
        """
        [{"id":"prefetch","llm_role":"none"},
         {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
         {"id":"score","tool":"risk_engine","llm_role":"none"},
         {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}]
        """));
    put(parse("clause_lookup", "2026.08.1", "One named retrieve stage",
        """
        [{"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"none"}]
        """));
    put(parse("template_retrieve", "2026.08.1", "Two named retrieve stages plus score",
        """
        [{"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"none"},
         {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
         {"id":"score","tool":"risk_engine","llm_role":"none"}]
        """));
    put(msaRiskReview());
    put(kycOnboarding());
    put(parse("claims_adjudicate", "2026.08.1", "Forced playbook retrieve then named clause retrieve",
        """
        [{"id":"pack_playbook","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
         {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
         {"id":"score","tool":"risk_engine","llm_role":"none"},
         {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}]
        """));
    put(parse("ticket_triage", "2026.08.1", "Fixed stages, flexible non-retrieve tools in Analyse",
        """
        [{"id":"extract","allowlist":["parse_ticket"],"max_tool_calls":2},
         {"id":"analyse","allowlist":["parse_ticket","tag_intent"],"max_tool_calls":4},
         {"id":"reply","allowlist":["draft_reply"],"max_tool_calls":2}]
        """));
    put(parse("product_explain", "2026.08.1", "Prefetch product terms, no retrieve tools",
        """
        [{"id":"extract","allowlist":["score_offer"],"max_tool_calls":2},
         {"id":"analyse","allowlist":["score_offer","compare_options"],"max_tool_calls":4},
         {"id":"explain","allowlist":["compare_options"],"max_tool_calls":2}]
        """));
    put(parse("narrow_review", "2026.08.1", "Analyse allowlists one retrieve tool",
        """
        [{"id":"extract","tool":"ocr_extract","llm_role":"none"},
         {"id":"analyse","allowlist":["clause_search","risk_engine"],"max_tool_calls":4},
         {"id":"report","tool":"draft_memo","llm_role":"synthesis"}]
        """));
    put(contractReview());
    put(parse("due_diligence", "2026.08.1", "Forced playbook retrieve then allowlisted retrieve",
        """
        [{"id":"extract","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
         {"id":"analyse","allowlist":["clause_search","policy_search","risk_engine"],"max_tool_calls":8},
         {"id":"report","tool":"draft_memo","llm_role":"synthesis"}]
        """));
    return this;
  }

  public static Workflow kycOnboarding() {
    return parse(
        "kyc_onboarding",
        "2026.08.1",
        "Fixed KYC onboarding stages with a risk branch and gated activation",
        """
        [
          {"id":"collect_docs","tool":"doc_intake"},
          {"id":"identity_check","tool":"id_verify"},
          {"id":"sanctions_screen","tool":"sanctions_api"},
          {"id":"risk_score","tool":"kyc_risk_engine","branch":{"high":"manual_review","low":"activate_account"}},
          {"id":"manual_review","type":"human_gate"},
          {"id":"activate_account","tool":"account_activate","side_effect":true,"requires_approval":true}
        ]
        """);
  }

  public static Workflow msaRiskReview() {
    return parse(
        "msa_risk_review",
        "2026.08.1",
        "Fixed MSA risk review stages: OCR, retrieve, score, memo",
        """
        [
          {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
          {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
          {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"query_formulation"},
          {"id":"risk_engine","tool":"risk_engine","llm_role":"none"},
          {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}
        ]
        """);
  }

  public static Workflow contractReview() {
    return parse(
        "contract_review",
        "2026.08.1",
        "Pattern 3: Extract → Analyse (allowlisted tools) → Generate Report",
        """
        [
          {"id":"extract","tool":"ocr_extract","llm_role":"none"},
          {"id":"analyse","allowlist":["clause_search","policy_search","risk_engine"],"max_tool_calls":6},
          {"id":"report","tool":"draft_memo","llm_role":"synthesis"}
        ]
        """);
  }

  private static Workflow parse(String id, String version, String description, String stagesJson) {
    return MAPPER.parse(id, version, description, stagesJson, "published");
  }

  private void put(Workflow workflow) {
    rows.put(key(workflow.workflowId(), workflow.workflowVersion()), workflow);
  }

  @Override
  public Optional<Workflow> find(String workflowId, String workflowVersion) {
    return Optional.ofNullable(rows.get(key(workflowId, workflowVersion)));
  }

  @Override
  public List<Workflow> listLatest() {
    Map<String, Workflow> latest = new HashMap<>();
    for (Workflow row : rows.values()) {
      Workflow existing = latest.get(row.workflowId());
      if (existing == null
          || CatalogVersion.compare(row.workflowVersion(), existing.workflowVersion()) > 0) {
        latest.put(row.workflowId(), row);
      }
    }
    return latest.values().stream()
        .sorted(Comparator.comparing(Workflow::workflowId))
        .toList();
  }

  @Override
  public List<Workflow> listAll() {
    return rows.values().stream()
        .sorted(
            Comparator.comparing(Workflow::workflowId)
                .thenComparing(
                    (a, b) -> CatalogVersion.compare(b.workflowVersion(), a.workflowVersion())))
        .toList();
  }

  @Override
  public List<Workflow> listVersions(String workflowId) {
    return rows.values().stream()
        .filter(row -> row.workflowId().equals(workflowId))
        .sorted((a, b) -> CatalogVersion.compare(b.workflowVersion(), a.workflowVersion()))
        .toList();
  }

  private static String key(String workflowId, String workflowVersion) {
    return workflowId + "@" + workflowVersion;
  }
}
