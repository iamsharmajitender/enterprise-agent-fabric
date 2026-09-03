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

  public InMemoryWorkflowStore seedEvalBoard() {
    return seedDemo();
  }

  public InMemoryWorkflowStore seedDemo() {
    put(parse("llm_pipeline", "2026.08.1", "Pattern 2: three LLM stages (classify then two synthesis). No domain HTTP.",
        """
        [{"id":"extract","llm_role":"classify"},{"id":"rewrite","llm_role":"synthesis"},{"id":"format","llm_role":"synthesis"}]
        """));
    put(parse("policy_memo", "2026.08.1", "Pattern 2: prefetch placeholder then one synthesis call. No domain HTTP.",
        """
        [{"id":"prefetch","llm_role":"none"},{"id":"generate","llm_role":"synthesis"}]
        """));
    put(parse("account_notify", "2026.08.1", "Pattern 2: one domain HTTP notify, then synthesis confirm.",
        """
        [{"id":"notify","tool":"notify_customer","llm_role":"none"},
         {"id":"respond","llm_role":"synthesis"}]
        """));
    put(parse("card_freeze", "2026.08.1", "Pattern 2: three domain HTTP writes, then synthesis confirm.",
        """
        [{"id":"identity","tool":"identity_check","llm_role":"none"},
         {"id":"limits","tool":"limit_check","llm_role":"none"},
         {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true},
         {"id":"respond","llm_role":"synthesis"}]
        """));
    put(parse("dispute_intake", "2026.08.1", "Pattern 2: two domain HTTP steps, then synthesis on the packet.",
        """
        [{"id":"intake","tool":"doc_intake","llm_role":"none"},
         {"id":"open","tool":"case_open","llm_role":"none"},
         {"id":"summarize","tool":"packet_summarize","llm_role":"synthesis"}]
        """));
    put(parse("purchase_refund", "2026.08.1", "Pattern 2: OCR, classify receipt JSON, match, eligibility, gated refund. human_gate is catalogue-only.",
        """
        [{"id":"ocr","tool":"ocr_extract","llm_role":"none"},
         {"id":"extract_fields","tool":"extract_fields","llm_role":"classify"},
         {"id":"match_purchase","tool":"match_purchase","llm_role":"none"},
         {"id":"eligibility","tool":"refund_eligibility","llm_role":"none"},
         {"id":"manual_review","type":"human_gate"},
         {"id":"post_refund","tool":"post_refund","llm_role":"none","side_effect":true,"requires_approval":true},
         {"id":"respond","tool":"refund_confirm","llm_role":"synthesis"}]
        """));
    put(parse("pack_then_notify", "2026.08.1", "Pattern 2: prefetch placeholder, domain notify, then synthesis confirm.",
        """
        [{"id":"prefetch","llm_role":"none"},
         {"id":"notify","tool":"notify_customer","llm_role":"none"},
         {"id":"respond","llm_role":"synthesis"}]
        """));
    put(parse("pack_then_freeze", "2026.08.1", "Pattern 2: prefetch placeholder, three domain HTTP writes, then synthesis confirm.",
        """
        [{"id":"prefetch","llm_role":"none"},
         {"id":"identity","tool":"identity_check","llm_role":"none"},
         {"id":"limits","tool":"limit_check","llm_role":"none"},
         {"id":"freeze","tool":"freeze_card","llm_role":"none","side_effect":true,"requires_approval":true},
         {"id":"respond","llm_role":"synthesis"}]
        """));
    put(parse("pack_then_review", "2026.08.1", "Pattern 2: prefetch placeholder, two domain HTTP tools, then synthesis memo.",
        """
        [{"id":"prefetch","llm_role":"none"},
         {"id":"ocr","tool":"ocr_extract","llm_role":"none"},
         {"id":"score","tool":"risk_engine","llm_role":"none"},
         {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}]
        """));
    put(parse("clause_lookup", "2026.08.1", "Pattern 2: LLM writes the retrieve query, HTTP search, then synthesis.",
        """
        [{"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
         {"id":"respond","llm_role":"synthesis"}]
        """));
    put(parse("template_retrieve", "2026.08.1", "Pattern 2: two query_formulation retrieves, HTTP score, then synthesis.",
        """
        [{"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
         {"id":"policy_search","tool":"policy_search","corpus":"legal-playbook","llm_role":"query_formulation"},
         {"id":"score","tool":"risk_engine","llm_role":"none"},
         {"id":"respond","llm_role":"synthesis"}]
        """));
    put(msaRiskReview());
    put(kycOnboarding());
    put(duplicateChargeReview());
    put(parse("claims_adjudicate", "2026.08.1", "Forced playbook retrieve then named clause retrieve",
        """
        [{"id":"pack_playbook","tool":"policy_search","corpus":"legal-playbook","llm_role":"none"},
         {"id":"clause_search","tool":"clause_search","corpus":"clause-index","llm_role":"query_formulation"},
         {"id":"score","tool":"risk_engine","llm_role":"none"},
         {"id":"memo","tool":"draft_memo","llm_role":"synthesis"}]
        """));
    put(parse("ticket_triage", "2026.08.1", "Pattern 3: parse ticket, tag intent, then draft_reply.",
        """
        [{"id":"extract","tool":"parse_ticket","llm_role":"none","allowlist":["parse_ticket"],"max_tool_calls":2},
         {"id":"analyse","tool":"tag_intent","llm_role":"none","allowlist":["parse_ticket","tag_intent"],"max_tool_calls":4},
         {"id":"reply","tool":"draft_reply","llm_role":"none","allowlist":["draft_reply"],"max_tool_calls":2}]
        """));
    put(parse("product_explain", "2026.08.1", "Pattern 3: prefetch placeholder, HTTP score/compare, then synthesis. Allowlists are catalogue-only.",
        """
        [{"id":"extract","tool":"score_offer","llm_role":"none","allowlist":["score_offer"],"max_tool_calls":2},
         {"id":"analyse","tool":"compare_options","llm_role":"none","allowlist":["score_offer","compare_options"],"max_tool_calls":4},
         {"id":"explain","llm_role":"synthesis","allowlist":["compare_options"],"max_tool_calls":2}]
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

  public static Workflow duplicateChargeReview() {
    return parse(
        "duplicate_charge_review",
        "2026.08.1",
        "Pattern 2: classify order id, lookup order, duplicate check, synthesis reply",
        """
        [
          {"id":"intake","tool":"duplicate_charge_intake","llm_role":"classify"},
          {"id":"order_lookup","tool":"lookup_order_by_order_id","llm_role":"none"},
          {"id":"dup_check","tool":"investigate_duplicate_charge","llm_role":"none"},
          {"id":"respond","tool":"duplicate_charge_respond","llm_role":"synthesis"}
        ]
        """);
  }

  public static Workflow kycOnboarding() {
    return parse(
        "kyc_onboarding",
        "2026.08.1",
        "Pattern 2: domain HTTP KYC tools then synthesis packet. branch and human_gate are catalogue-only.",
        """
        [
          {"id":"collect_docs","tool":"doc_intake","llm_role":"none"},
          {"id":"identity_check","tool":"id_verify","llm_role":"none"},
          {"id":"sanctions_screen","tool":"sanctions_api","llm_role":"none"},
          {"id":"risk_score","tool":"kyc_risk_engine","llm_role":"none","branch":{"high":"manual_review","low":"activate_account"}},
          {"id":"manual_review","type":"human_gate"},
          {"id":"activate_account","tool":"account_activate","llm_role":"none","side_effect":true,"requires_approval":true},
          {"id":"summarize","llm_role":"synthesis"}
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
