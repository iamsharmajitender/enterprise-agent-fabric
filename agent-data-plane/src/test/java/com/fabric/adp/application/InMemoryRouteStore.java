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
        "One LLM call. Prompt only. Pattern 0 cannot take tools, retrieve tools, or a workflow. No memory, no retrieval.",
        RUNS, null, null, null, "low_risk_chat", ModelProfile.LIGHTWEIGHT_CHAT, null, "agent-chat",
        null, null, 1, "clarify", List.of(), List.of("web"), true, List.of("hello", "hi", "chat"));
    add("email_summarize", 0, "summarize_email",
        "One LLM call. Prompt, output schema, eval. No tools, no workflow, no retrieval, no memory. Summarize the pasted email.",
        RUNS, null, null, null, "read_only_standard", ModelProfile.FAST_CHAT, null, "email_summarize",
        "exec_bullets", "email_summarize_golden", 1, "clarify", List.of(), List.of("api"), false, List.of());
    add("chat_session", 0, "chat_session",
        "One LLM call per turn with session conversation memory. Still no tools, no retrieve, no workflow. Memory is the only extra artefact.",
        RUNS, null, null, conversationMemory(), "low_risk_chat", ModelProfile.LIGHTWEIGHT_CHAT, null, "chat_session",
        null, null, 1, "clarify", List.of(), List.of("web"), true, List.of("hello", "hi", "chat"));
    add("agent-policy-qa", 0, "policy_qa",
        "App prefetches policy-engine and product-faq, then one grounded answer. No tools, no retrieve tool, no workflow, no memory.",
        RUNS, null, new Retrieval("deterministic_prefetch", List.of("policy-engine", "product-faq")), null,
        "read_only_standard", ModelProfile.FAST_CHAT, null, "agent-policy-qa",
        "cited_answer", "policy_qa_golden", 1, "clarify", List.of("policy:read"), List.of("web"), true,
        List.of("policy", "procedure", "handbook"));
    add("policy_chat", 0, "policy_chat",
        "Prefetch of policy-engine plus session memory. Still Pattern 0: one call per turn, no tools, no workflow, no retrieve tool.",
        RUNS, null, new Retrieval("deterministic_prefetch", List.of("policy-engine")), conversationMemory(),
        "read_only_standard", ModelProfile.FAST_CHAT, null, "policy_chat",
        "cited_answer", "policy_qa_golden", 1, "clarify", List.of("policy:read"), List.of("web"), true,
        List.of("policy", "handbook"));
    add("search_only", 1, "search_only",
        "Open loop with one tool (web_search). Prompt, memory, max_loop_steps. No workflow. No corpus prefetch and no retrieve tool.",
        RUNS, InMemoryManifestStore.searchOnly(), null, loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "search_only",
        null, null, 8, "clarify", List.of(), List.of("web"), true, List.of("search", "google"));
    add("research_assistant", 1, "research_topic",
        "Open loop with multiple tools (web_search, fetch_url, note_store, draft_brief). Prompt and memory. No workflow. No corpus RAG — tools are not retrieve-from-index.",
        RUNS, InMemoryManifestStore.researchAssistant(), null, loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "research_assistant",
        "research_brief", "research_assistant_golden", 16, "clarify", List.of(), List.of("web"), true,
        List.of("research", "sources"));
    add("fraud_one_tool", 1, "fraud_one_tool",
        "Case file is prefetched, then the model may call one non-retrieve tool (draft_memo). Prompt, memory, no workflow. Retrieval.mode is prefetch.",
        RUNS, InMemoryManifestStore.fraudOneTool(), new Retrieval("deterministic_prefetch", List.of("accounts")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, null, "fraud_one_tool",
        "risk_memo", null, 6, "clarify", List.of("fraud:read"), List.of("api"), false, List.of());
    add("fraud_casefile", 1, "fraud_casefile",
        "Case file is prefetched, then the model loops across multiple non-retrieve tools (ocr_extract, risk_engine, draft_memo). Prompt, memory, no workflow. No retrieve tool on the manifest.",
        RUNS, InMemoryManifestStore.fraudCasefile(), new Retrieval("deterministic_prefetch", List.of("accounts")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, null, "fraud_casefile",
        "risk_memo", null, 10, "clarify", List.of("fraud:read"), List.of("api"), false, List.of());
    add("fee_explain", 1, "fee_explain",
        "Open loop with one retrieve tool (account_fee_lookup) over accounts. Prompt, memory, max_loop_steps. No workflow.",
        RUNS, InMemoryManifestStore.feeExplain(), new Retrieval("tool", List.of("accounts")), loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "fee_explain",
        "fee_explain_out", "fee_explain_golden", 6, "clarify", List.of("accounts:read"), List.of("web"), true,
        List.of("fee", "charged", "charge", "42", "monthly"));
    add("contract_investigation", 1, "contract_investigate",
        "Open loop with multiple tools including two retrieve tools (ocr_extract, clause_search, policy_search, risk_engine, draft_memo). Tool-mode over clause-index and legal-playbook. Prompt, memory, no workflow.",
        RUNS, InMemoryManifestStore.contractInvestigate(), new Retrieval("tool", List.of("clause-index", "legal-playbook")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, null, "contract_investigate",
        "risk_memo", "contract_investigate_golden", 12, "clarify", List.of("legal:read"), List.of("api"), false,
        List.of());
    add("fraud_investigate", 1, "fraud_investigate",
        "Open loop with domain tools plus one agent capability (start_contract_review → contract_review). Child jobs POST is catalogue-only.",
        RUNS, InMemoryManifestStore.fraudInvestigate(), null, loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "fraud_investigate",
        "risk_memo", null, 8, "clarify", List.of("fraud:read"), List.of("api"), false, List.of());
    add("ops_start_kyc", 1, "ops_start_kyc",
        "Open loop with parse_ticket plus one agent capability (start_kyc_onboarding → kyc_onboarding). Child jobs POST is catalogue-only.",
        RUNS, InMemoryManifestStore.opsStartKyc(), null, loopMemory("none", 8),
        "read_only_standard", ModelProfile.REASONING_STANDARD, null, "ops_start_kyc",
        null, null, 6, "clarify", List.of("kyc:onboard"), List.of("api"), false, List.of());
    add("llm_pipeline", 2, "llm_pipeline",
        "Fixed LLM stages (extract → rewrite → format). Workflow and prompt only. No tools, no prefetch, no retrieve, no memory.",
        RUNS, null, null, null, "read_only_standard", ModelProfile.FAST_CHAT, "llm_pipeline", "llm_pipeline",
        null, null, null, "clarify", List.of(), List.of("api"), false, List.of());
    add("policy_memo", 2, "policy_memo",
        "Fixed retrieve-then-generate workflow. App prefetches the corpus; generate uses the prompt. No tools, no retrieve tool, no memory. Model cannot skip prefetch.",
        RUNS, null, new Retrieval("deterministic_prefetch", List.of("policy-engine")), null,
        "read_only_standard", ModelProfile.REASONING_STANDARD, "policy_memo", "policy_memo",
        "msa_memo", null, null, "clarify", List.of("policy:read"), List.of("api"), false, List.of());
    add("account_notify", 2, "account_notify",
        "Fixed one-tool write (notify_customer). Workflow and manifest. No prompt, no prefetch, no retrieve, no memory. llm_role none.",
        RUNS, InMemoryManifestStore.accountNotify(), null, null, "high_risk_step_up", ModelProfile.REASONING_STANDARD,
        "account_notify", null, null, null, null, "escalate_human", List.of("notify:send"), List.of("api"), false,
        List.of());
    add("card_freeze", 2, "card_freeze",
        "Fixed multi-tool write: identity_check → limit_check → freeze_card. Workflow and manifest. No prompt, no prefetch, no retrieve, no memory. Freeze is a gated side effect.",
        RUNS, InMemoryManifestStore.cardFreeze(), null, null, "high_risk_step_up", ModelProfile.REASONING_STANDARD,
        "card_freeze", null, null, null, null, "escalate_human", List.of("cards:freeze"), List.of("api"), false,
        List.of());
    add("dispute_intake", 2, "dispute_intake",
        "Fixed multi-tool dispute chain (doc_intake, case_open, packet_summarize). Workflow, prompt on the packet, memory. No prefetch and no retrieve tool.",
        RUNS, InMemoryManifestStore.disputeIntake(), null, loopMemory("none", 8), "read_only_standard",
        ModelProfile.REASONING_STANDARD, "dispute_intake", "dispute_intake",
        null, null, null, "clarify", List.of("disputes:write"), List.of("api"), false, List.of());
    add("pack_then_notify", 2, "pack_then_notify",
        "Prefetch product/limit policy, then one tool (notify_customer). Workflow, no prompt, no retrieve tool, no memory.",
        RUNS, InMemoryManifestStore.accountNotify(), new Retrieval("deterministic_prefetch", List.of("product-terms")),
        null, "high_risk_step_up", ModelProfile.REASONING_STANDARD, "pack_then_notify", null,
        null, null, null, "escalate_human", List.of("notify:send"), List.of("api"), false, List.of());
    add("pack_then_freeze", 2, "pack_then_freeze",
        "Prefetch product/limit policy, then multiple tool-only stages (identity_check, limit_check, freeze_card). Workflow, no prompt, no retrieve tool, no memory.",
        RUNS, InMemoryManifestStore.cardFreeze(), new Retrieval("deterministic_prefetch", List.of("product-terms")),
        null, "high_risk_step_up", ModelProfile.REASONING_STANDARD, "pack_then_freeze", null,
        null, null, null, "escalate_human", List.of("cards:freeze"), List.of("api"), false, List.of());
    add("pack_then_review", 2, "pack_then_review",
        "Prefetch the playbook, then multiple fixed tools, then an LLM memo. Workflow, prompt on memo, memory. Retrieve is not a tool — mode is prefetch.",
        RUNS, InMemoryManifestStore.packThenReview(), new Retrieval("deterministic_prefetch", List.of("legal-playbook")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "pack_then_review", "pack_then_review",
        "msa_memo", null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("clause_lookup", 2, "clause_lookup",
        "One named retrieve stage (clause_search) with a templated query. Workflow and one retrieve tool. No prompt, no prefetch, no memory. llm_role none.",
        RUNS, InMemoryManifestStore.clauseLookup(), new Retrieval("tool", List.of("clause-index")), null,
        "read_only_standard", ModelProfile.REASONING_STANDARD, "clause_lookup", null,
        null, null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("template_retrieve", 2, "template_retrieve",
        "Two named retrieve stages (clause_search then policy_search) plus score. Multiple retrieve tools, templated queries. Workflow, no prompt, no prefetch, no memory.",
        RUNS, InMemoryManifestStore.templateRetrieve(), new Retrieval("tool", List.of("clause-index", "legal-playbook")),
        null, "read_only_standard", ModelProfile.REASONING_STANDARD, "template_retrieve", null,
        null, null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("msa_risk_review", 2, "msa_risk_review",
        "Fixed OCR → clause_search → policy_search → risk_engine → draft_memo. Multiple tools, two of them retrieve. Workflow, prompt on query/memo, memory. No prefetch — retrieve is named stages.",
        RUNS, InMemoryManifestStore.msaRiskReview(), new Retrieval("tool", List.of("clause-index", "legal-playbook")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "msa_risk_review", "msa_risk_review",
        "msa_memo", "msa_risk_review_golden", null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("kyc_onboarding", 2, "kyc_onboard",
        "Fixed KYC: doc_intake, id_verify, sanctions_api, risk, human gate, activate. Multiple tools, tool retrieve over sanctions-lists and kyc-policy. Workflow, prompt on the review packet, memory.",
        RUNS, InMemoryManifestStore.kycOnboarding(), new Retrieval("tool", List.of("sanctions-lists", "kyc-policy")),
        loopMemory("none", 8), "high_risk_step_up", ModelProfile.REASONING_STANDARD, "kyc_onboarding",
        "kyc_onboarding", "kyc_result", "kyc_onboarding_golden", null, "escalate_human",
        List.of("kyc:onboard"), List.of("api"), false, List.of());
    add("claims_adjudicate", 2, "claims_adjudicate",
        "Workflow with multiple tools. First stage always retrieves legal-playbook (forced pack). Later named stage retrieves clause-index. Prompt on memo, memory. One retrieval.mode (tool); prefetch is a designer-forced retrieve stage, not a second mode.",
        RUNS, InMemoryManifestStore.claimsAdjudicate(), new Retrieval("tool", List.of("legal-playbook", "clause-index")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "claims_adjudicate",
        "claims_adjudicate", "msa_memo", null, null, "clarify", List.of("claims:read"), List.of("api"), false,
        List.of());
    add("ticket_triage", 3, "ticket_triage",
        "Fixed Extract → Analyse → Reply. Multiple allowlisted tools per stage (parse_ticket, tag_intent, draft_reply). Workflow, prompt, memory. No prefetch, no retrieve tool.",
        RUNS, InMemoryManifestStore.ticketTriage(), null, loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, "ticket_triage", "ticket_triage",
        null, null, null, "clarify", List.of(), List.of("api"), false, List.of());
    add("product_explain", 3, "product_explain",
        "Fixed stages. App prefetches product-terms and fee-schedule. Analyse allowlist is multiple non-retrieve tools (score_offer, compare_options). Workflow, prompt, memory. No retrieve tool.",
        RUNS, InMemoryManifestStore.productExplain(), new Retrieval("deterministic_prefetch", List.of("product-terms", "fee-schedule")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "product_explain", "product_explain",
        null, null, null, "clarify", List.of("policy:read"), List.of("web"), true, List.of("loan", "offer", "product"));
    add("narrow_review", 3, "narrow_review",
        "Fixed Extract → Analyse → Report. Multiple tools overall, but Analyse allowlists one retrieve tool (clause_search) plus risk_engine. Workflow, prompt, memory. Tool-mode, stage-scoped. No prefetch.",
        RUNS, InMemoryManifestStore.narrowReview(), new Retrieval("tool", List.of("clause-index")), loopMemory(),
        "read_only_standard", ModelProfile.REASONING_STANDARD, "narrow_review", "narrow_review",
        "counsel_memo", null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
    add("contract_review", 3, "contract_review",
        "Fixed Extract → Analyse → Report. Multiple tools including multiple retrieve tools (clause_search, policy_search, risk_engine). Workflow, prompt, memory, output, eval. Tool-mode, stage-scoped. No prefetch.",
        RUNS, InMemoryManifestStore.contractReview(), new Retrieval("tool", List.of("clause-index", "legal-playbook")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "contract_review", "contract_review",
        "counsel_memo", "contract_review_golden", null, "clarify", List.of("legal:read"), List.of("api"), false,
        List.of());
    add("due_diligence", 3, "due_diligence",
        "Workflow, multiple tools, memory, prompt. Extract always retrieves legal-playbook (forced). Analyse may retrieve again (clause_search, policy_search). One retrieval.mode (tool). This is prefetch-as-a-stage plus retrieve tools.",
        RUNS, InMemoryManifestStore.dueDiligence(), new Retrieval("tool", List.of("legal-playbook", "clause-index")),
        loopMemory(), "read_only_standard", ModelProfile.REASONING_STANDARD, "due_diligence", "due_diligence",
        "counsel_memo", null, null, "clarify", List.of("legal:read"), List.of("api"), false, List.of());
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
