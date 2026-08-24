package com.fabric.adp.application;

import com.fabric.adp.domain.AutonomyPattern;
import com.fabric.adp.domain.MemoryProfile;
import com.fabric.adp.domain.ModelProfile;
import com.fabric.adp.domain.Retrieval;
import com.fabric.adp.domain.RouteRow;
import com.fabric.adp.domain.ToolManifest;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CopyOnWriteArrayList;

public class InMemoryRouteStore implements RouteStore {

  private static final String RUNS = "http://agent-runtime:3008/v1/runs";
  private static final String V = "2026.08.1";

  private final List<RouteRow> routes = new CopyOnWriteArrayList<>();

  public InMemoryRouteStore seedDemo() {
    add("agent-chat", 0, "general_chat",
        "Pattern 0 (single inference): one LLM call from host. No tools, no workflow, no memory, no retrieval.",
        RUNS, null, null, null, "low_risk_chat", ModelProfile.LIGHTWEIGHT_CHAT, null, "agent-chat",
        null, null, 1, "clarify", List.of(), List.of("web"), true, List.of("hello", "hi", "chat"));
    add("email_summarize", 0, "summarize_email",
        "Pattern 0 (single inference): one LLM call from host. Summarize the pasted email. Prompt plus output schema. No tools, no workflow.",
        RUNS, null, null, null, "read_only_standard", ModelProfile.FAST_CHAT, null, "email_summarize",
        "exec_bullets", "email_summarize_golden", 1, "clarify", List.of(), List.of("api"), false, List.of());
    add("chat_session", 0, "chat_session",
        "Pattern 0 (single inference): one LLM call per turn from host. Session conversation memory. No tools, no workflow.",
        RUNS, null, null, conversationMemory(), "low_risk_chat", ModelProfile.LIGHTWEIGHT_CHAT, null, "chat_session",
        null, null, 1, "clarify", List.of(), List.of("web"), true, List.of("hello", "hi", "chat"));
    add("agent-policy-qa", 0, "policy_qa",
        "Pattern 0 (single inference): one LLM call from host after catalogue prefetch of policy-engine and product-faq. Prefetch is not packed today. No tools, no workflow.",
        RUNS, null, new Retrieval("deterministic_prefetch", List.of("policy-engine", "product-faq")), null,
        "read_only_standard", ModelProfile.FAST_CHAT, null, "agent-policy-qa",
        "cited_answer", "policy_qa_golden", 1, "clarify", List.of("policy:read"), List.of("web"), true,
        List.of("policy", "procedure", "handbook"));
    add("policy_chat", 0, "policy_chat",
        "Pattern 0 (single inference): one LLM call per turn from host. Catalogue prefetch of policy-engine plus session memory. No tools, no workflow.",
        RUNS, null, new Retrieval("deterministic_prefetch", List.of("policy-engine")), conversationMemory(),
        "read_only_standard", ModelProfile.FAST_CHAT, null, "policy_chat",
        "cited_answer", "policy_qa_golden", 1, "clarify", List.of("policy:read"), List.of("web"), true,
        List.of("policy", "handbook"));
    add("search_only", 1, "search_only",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over web_search, up to max_loop_steps. One host prompt reused each turn. No workflow.",
        RUNS, InMemoryManifestStore.searchOnly(), null, loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "search_only",
        null, null, 8, "clarify", List.of(), List.of("web"), true, List.of("search", "google"));
    add("research_assistant", 1, "research_topic",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over web_search, fetch_url, note_store, draft_brief. One host prompt reused each turn. No workflow.",
        RUNS, InMemoryManifestStore.researchAssistant(), null, loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "research_assistant",
        "research_brief", "research_assistant_golden", 16, "clarify", List.of(), List.of("web"), true,
        List.of("research", "sources"));
    add("fraud_one_tool", 1, "fraud_one_tool",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over draft_memo after catalogue prefetch of accounts. One host prompt reused each turn. No workflow.",
        RUNS, InMemoryManifestStore.fraudOneTool(), new Retrieval("deterministic_prefetch", List.of("accounts")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, null, "fraud_one_tool",
        "risk_memo", null, 6, "clarify", List.of("fraud:read"), List.of("api"), false, List.of());
    add("fraud_casefile", 1, "fraud_casefile",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, risk_engine, draft_memo after catalogue prefetch. One host prompt reused each turn. No workflow.",
        RUNS, InMemoryManifestStore.fraudCasefile(), new Retrieval("deterministic_prefetch", List.of("accounts")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, null, "fraud_casefile",
        "risk_memo", null, 10, "clarify", List.of("fraud:read"), List.of("api"), false, List.of());
    add("fee_explain", 1, "fee_explain",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over account_fee_lookup. One host prompt reused each turn. Domain HTTP only on CALL. No workflow.",
        RUNS, InMemoryManifestStore.feeExplain(), new Retrieval("tool", List.of("accounts")), loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "fee_explain",
        "fee_explain_out", "fee_explain_golden", 6, "clarify", List.of("accounts:read"), List.of("web"), true,
        List.of("fee", "charged", "charge", "42", "monthly"));
    add("contract_investigation", 1, "contract_investigate",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, clause_search, policy_search, risk_engine, draft_memo. One host prompt reused each turn. No workflow.",
        RUNS, InMemoryManifestStore.contractInvestigate(), new Retrieval("tool", List.of("clause-index", "legal-playbook")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, null, "contract_investigate",
        "risk_memo", "contract_investigate_golden", 12, "clarify", List.of("legal:read"), List.of("api"), false,
        List.of());
    add("fraud_investigate", 1, "fraud_investigate",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over ocr_extract, draft_memo, start_contract_review. One host prompt reused each turn. kind=agent child start is catalogue-only. No workflow.",
        RUNS, InMemoryManifestStore.fraudInvestigate(), null, loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "fraud_investigate",
        "risk_memo", null, 8, "clarify", List.of("fraud:read"), List.of("api"), false, List.of());
    add("ops_start_kyc", 1, "ops_start_kyc",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over parse_ticket and start_kyc_onboarding. One host prompt reused each turn. kind=agent child start is catalogue-only. No workflow.",
        RUNS, InMemoryManifestStore.opsStartKyc(), null, loopMemory("none", 8),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "ops_start_kyc",
        null, null, 6, "clarify", List.of("kyc:onboard"), List.of("api"), false, List.of());
    add("llm_pipeline", 2, "llm_pipeline",
        "Pattern 2 (deterministic): fixed workflow of three LLM stages. Prompts: host plus classify and synthesis templates. No domain HTTP.",
        RUNS, null, null, null, "read_only_standard", ModelProfile.FAST_CHAT, "llm_pipeline", "llm_pipeline",
        null, null, null, "clarify", List.of(), List.of("api"), false, List.of());
    add("policy_memo", 2, "policy_memo",
        "Pattern 2 (deterministic): prefetch placeholder then one synthesis call. Prompts: host plus synthesis template. Prefetch is not packed today.",
        RUNS, null, new Retrieval("deterministic_prefetch", List.of("policy-engine")), null,
        "read_only_standard", ModelProfile.REASONING_STANDARD, "policy_memo", "policy_memo",
        "msa_memo", null, null, "clarify", List.of("policy:read"), List.of("api"), false, List.of());
    add("account_notify", 2, "account_notify",
        "Pattern 2 (deterministic): domain HTTP notify_customer, then synthesis confirm. Prompts: host plus synthesis template.",
        RUNS, InMemoryManifestStore.accountNotify(), null, null, "high_risk_step_up", ModelProfile.REASONING_STANDARD,
        "account_notify", "account_notify", null, null, null, "escalate_human", List.of("notify:send"), List.of("api"), false,
        List.of());
    add("card_freeze", 2, "card_freeze",
        "Pattern 2 (deterministic): domain HTTP identity_check, limit_check, freeze_card, then synthesis confirm. Prompts: host plus synthesis template. Freeze remains a gated side effect in catalogue.",
        RUNS, InMemoryManifestStore.cardFreeze(), null, null, "high_risk_step_up", ModelProfile.REASONING_STANDARD,
        "card_freeze", "card_freeze", null, null, null, "escalate_human", List.of("cards:freeze"), List.of("api"), false,
        List.of());
    add("dispute_intake", 2, "dispute_intake",
        "Pattern 2 (deterministic): two domain HTTP steps then synthesis on packet_summarize. Prompts: host plus synthesis template.",
        RUNS, InMemoryManifestStore.disputeIntake(), null, loopMemory("none", 8), "read_only_standard",
        ModelProfile.REASONING_STANDARD, "dispute_intake", "dispute_intake",
        null, null, null, "clarify", List.of("disputes:write"), List.of("api"), false, List.of());
    add("pack_then_notify", 2, "pack_then_notify",
        "Pattern 2 (deterministic): prefetch placeholder, domain HTTP notify, then synthesis confirm. Prompts: host plus synthesis template. Prefetch is not packed today.",
        RUNS, InMemoryManifestStore.accountNotify(), new Retrieval("deterministic_prefetch", List.of("product-terms")),
        null, "high_risk_step_up", ModelProfile.REASONING_STANDARD, "pack_then_notify", "pack_then_notify",
        null, null, null, "escalate_human", List.of("notify:send"), List.of("api"), false, List.of());
    add("pack_then_freeze", 2, "pack_then_freeze",
        "Pattern 2 (deterministic): prefetch placeholder, three domain HTTP writes, then synthesis confirm. Prompts: host plus synthesis template. Prefetch is not packed today.",
        RUNS, InMemoryManifestStore.cardFreeze(), new Retrieval("deterministic_prefetch", List.of("product-terms")),
        null, "high_risk_step_up", ModelProfile.REASONING_STANDARD, "pack_then_freeze", "pack_then_freeze",
        null, null, null, "escalate_human", List.of("cards:freeze"), List.of("api"), false, List.of());
    add("pack_then_review", 2, "pack_then_review",
        "Pattern 2 (deterministic): prefetch placeholder, two domain HTTP tools, then synthesis memo. Prompts: host plus synthesis template. Prefetch is not packed today.",
        RUNS, InMemoryManifestStore.packThenReview(), new Retrieval("deterministic_prefetch", List.of("legal-playbook")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "pack_then_review", "pack_then_review",
        "msa_memo", null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("clause_lookup", 2, "clause_lookup",
        "Pattern 2 (deterministic): LLM query_formulation, HTTP clause_search, then synthesis. Prompts: host plus query_formulation and synthesis templates.",
        RUNS, InMemoryManifestStore.clauseLookup(), new Retrieval("tool", List.of("clause-index")), null,
        "read_only_standard", ModelProfile.REASONING_STANDARD, "clause_lookup", "clause_lookup",
        null, null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("template_retrieve", 2, "template_retrieve",
        "Pattern 2 (deterministic): two query_formulation retrieves, HTTP score, then synthesis. Prompts: host plus query_formulation and synthesis templates.",
        RUNS, InMemoryManifestStore.templateRetrieve(), new Retrieval("tool", List.of("clause-index", "legal-playbook")),
        null, "read_only_standard", ModelProfile.REASONING_STANDARD, "template_retrieve", "template_retrieve",
        null, null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("msa_risk_review", 2, "msa_risk_review",
        "Pattern 2 (deterministic): HTTP OCR, two query_formulation retrieves, HTTP score, synthesis memo. Prompts: host plus query_formulation and synthesis templates.",
        RUNS, InMemoryManifestStore.msaRiskReview(), new Retrieval("tool", List.of("clause-index", "legal-playbook")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "msa_risk_review", "msa_risk_review",
        "msa_memo", "msa_risk_review_golden", null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("kyc_onboarding", 2, "kyc_onboard",
        "Pattern 2 (deterministic): domain HTTP KYC tools then synthesis packet. Prompts: host plus synthesis template. branch and human_gate are catalogue-only.",
        RUNS, InMemoryManifestStore.kycOnboarding(), new Retrieval("tool", List.of("sanctions-lists", "kyc-policy")),
        loopMemory("none", 8), "high_risk_step_up", ModelProfile.REASONING_STANDARD, "kyc_onboarding",
        "kyc_onboarding", "kyc_result", "kyc_onboarding_golden", null, "escalate_human",
        List.of("kyc:onboard"), List.of("api"), false, List.of());
    add("claims_adjudicate", 2, "claims_adjudicate",
        "Pattern 2 (deterministic): HTTP playbook retrieve, query_formulation clause search, HTTP score, synthesis memo. Prompts: host plus query_formulation and synthesis templates.",
        RUNS, InMemoryManifestStore.claimsAdjudicate(), new Retrieval("tool", List.of("legal-playbook", "clause-index")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "claims_adjudicate",
        "claims_adjudicate", "msa_memo", null, null, "clarify", List.of("claims:read"), List.of("api"), false,
        List.of());
    add("ticket_triage", 3, "ticket_triage",
        "Pattern 3 (guided): HTTP parse and tag, then synthesis reply. Prompts: host plus synthesis template. Stage allowlists are catalogue-only.",
        RUNS, InMemoryManifestStore.ticketTriage(), null, loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, "ticket_triage", "ticket_triage",
        null, null, null, "clarify", List.of(), List.of("api"), false, List.of());
    add("product_explain", 3, "product_explain",
        "Pattern 3 (guided): prefetch placeholder, HTTP score/compare, then synthesis. Prompts: host plus synthesis template. Allowlists are catalogue-only. Prefetch is not packed today.",
        RUNS, InMemoryManifestStore.productExplain(), new Retrieval("deterministic_prefetch", List.of("product-terms", "fee-schedule")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "product_explain", "product_explain",
        null, null, null, "clarify", List.of("policy:read"), List.of("web"), true, List.of("loan", "offer", "product"));
    add("narrow_review", 3, "narrow_review",
        "Pattern 3 (guided): HTTP OCR, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.",
        RUNS, InMemoryManifestStore.narrowReview(), new Retrieval("tool", List.of("clause-index")), loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, "narrow_review", "narrow_review",
        "counsel_memo", null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("contract_review", 3, "contract_review",
        "Pattern 3 (guided): HTTP OCR, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.",
        RUNS, InMemoryManifestStore.contractReview(), new Retrieval("tool", List.of("clause-index", "legal-playbook")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "contract_review", "contract_review",
        "counsel_memo", "contract_review_golden", null, "clarify", List.of("legal:read"), List.of("api"), false,
        List.of());
    add("due_diligence", 3, "due_diligence",
        "Pattern 3 (guided): HTTP playbook extract, catalogue allowlist on Analyse, synthesis report. Prompts: host plus synthesis template. Allowlists are catalogue-only.",
        RUNS, InMemoryManifestStore.dueDiligence(), new Retrieval("tool", List.of("legal-playbook", "clause-index")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "due_diligence", "due_diligence",
        "counsel_memo", null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    return this;
  }

  public InMemoryRouteStore replace(RouteRow row) {
    routes.removeIf(
        existing ->
            existing.routeId().equals(row.routeId())
                && existing.routeVersion().equals(row.routeVersion()));
    routes.add(row);
    return this;
  }

  private void add(
      String id,
      int pattern,
      String intent,
      String description,
      String activation,
      ToolManifest manifest,
      Retrieval retrieval,
      MemoryProfile memory,
      String policy,
      ModelProfile model,
      String workflowId,
      String promptId,
      String outputSchema,
      String evalSuite,
      Integer maxLoop,
      String fallback,
      List<String> claims,
      List<String> channels,
      boolean chatVisible,
      List<String> keywords) {
    routes.add(
        new RouteRow(
            id,
            V,
            true,
            intent,
            description,
            activation,
            "agent-" + id,
            manifest,
            policy,
            model,
            retrieval,
            memory,
            workflowId,
            promptId,
            outputSchema,
            evalSuite,
            maxLoop,
            fallback,
            claims,
            channels,
            chatVisible,
            keywords,
            AutonomyPattern.fromCode(pattern)));
  }

  private static MemoryProfile conversationMemory() {
    return new MemoryProfile("session", "session", "none", "none", 24, List.of("tenant", "user", "session"));
  }

  private static MemoryProfile loopMemory() {
    return loopMemory("retrieve_only", 24);
  }

  private static MemoryProfile loopMemory(String longTerm, int ttlHours) {
    return new MemoryProfile(
        "session", "session", "checkpoint", longTerm, ttlHours, List.of("tenant", "user", "session"));
  }

  @Override
  public List<RouteRow> activeRoutes() {
    return routes.stream().filter(RouteRow::active).toList();
  }

  @Override
  public List<RouteRow> allRoutes() {
    return routes.stream()
        .sorted(
            Comparator.comparing(RouteRow::routeId)
                .thenComparing(Comparator.comparing(RouteRow::routeVersion).reversed()))
        .toList();
  }

  @Override
  public Optional<RouteRow> activeRoute(String routeId) {
    return routes.stream().filter(r -> r.routeId().equals(routeId) && r.active()).findFirst();
  }

  @Override
  public Optional<RouteRow> route(String routeId, String routeVersion) {
    return routes.stream()
        .filter(r -> r.routeId().equals(routeId) && r.routeVersion().equals(routeVersion))
        .findFirst();
  }

  @Override
  public List<RouteRow> versions(String routeId) {
    return routes.stream()
        .filter(r -> r.routeId().equals(routeId))
        .sorted(Comparator.comparing(RouteRow::routeVersion).reversed())
        .toList();
  }
}
