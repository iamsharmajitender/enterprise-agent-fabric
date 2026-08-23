package com.fabric.adp.application;

import com.fabric.adp.domain.PromptPack;
import com.fabric.adp.domain.PromptRoleTemplate;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class InMemoryPromptStore implements PromptStore {

  private final Map<String, PromptPack> rows = new LinkedHashMap<>();

  public InMemoryPromptStore seedDemo() {
    put(chat());
    put(emailSummarize());
    put(host("chat_session", "Continue the conversation. No tools. Do not invent facts."));
    put(policyQa());
    put(host("policy_chat", "Answer from prefetched policy chunks. Use session memory. No tools."));
    put(host("search_only", "Research with web_search only. Stop when the budget is exhausted."));
    put(host("research_assistant", "Research using only allowed tools. Prefer primary sources. Stop when the brief is evidence-backed or the budget is exhausted."));
    put(host("fraud_one_tool", "The case file is already in context. Draft a memo with draft_memo only.", "fraud-ops"));
    put(host("fraud_casefile", "The case file is already in context. Use OCR, risk, and draft tools. Do not retrieve corpora.", "fraud-ops"));
    put(host("fraud_investigate", "Investigate the case with OCR and memo tools. You may propose start_contract_review to hand Legal a separate jobs run. Do not invent tools.", "fraud-ops"));
    put(host("ops_start_kyc", "Parse the onboarding ticket. You may propose start_kyc_onboarding to hand KYC a separate jobs run. Do not invent tools.", "ops"));
    put(feeExplain());
    put(contractInvestigate());
    put(host("llm_pipeline", "Do only the current stage. Do not choose the next stage. No tools."));
    put(host("policy_memo", "Draft the memo from prefetched policy only. Do not skip retrieve."));
    put(host("dispute_intake", "Summarize the dispute packet. Do not open extra cases. Do not skip stages.", "ops"));
    put(host("pack_then_review", "The playbook is already packed. Draft the memo from stage outputs only.", "legal-agents"));
    put(msaRiskReview());
    put(kycOnboarding());
    put(host("claims_adjudicate", "Formulate the clause query or draft the memo. Do not reorder stages.", "claims-ops"));
    put(host("ticket_triage", "Stay inside the current stage. Inside Analyse pick parser/scorer tools. Do not invent stages.", "ops"));
    put(host("product_explain", "Product terms are already packed. Stay inside the current stage allowlist.", "product"));
    put(host("narrow_review", "Stay inside the current stage. Analyse may use clause_search and risk_engine only.", "legal-agents"));
    put(contractReview());
    put(host("due_diligence", "Extract always retrieves the playbook. Inside Analyse you may retrieve again. Do not invent stages.", "legal-agents"));
    return this;
  }

  private static PromptPack host(String promptId, String host) {
    return host(promptId, host, "assistant-platform");
  }

  private static PromptPack host(String promptId, String host, String owner) {
    return new PromptPack(promptId, "2026.08.1", host, "published", owner, List.of());
  }

  public static PromptPack msaRiskReview() {
    return new PromptPack(
        "msa_risk_review",
        "2026.08.1",
        "You are counsel's MSA risk-review worker. Do only the current stage. Do not choose the next stage. Do not invent tools.",
        "published",
        "legal-agents",
        List.of(
            new PromptRoleTemplate(
                "query_formulation",
                "plan",
                "Write the search query for this stage's corpus only. Do not pick a different index."),
            new PromptRoleTemplate(
                "synthesis",
                "synthesize",
                "Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.")));
  }

  public static PromptPack emailSummarize() {
    return new PromptPack(
        "email_summarize",
        "2026.08.1",
        "Summarize this email for the banker. No tools. Return short bullets.",
        "published",
        "assistant-platform",
        List.of());
  }

  public static PromptPack feeExplain() {
    return new PromptPack(
        "fee_explain",
        "2026.08.1",
        "You explain account fees. Use the fee lookup tool. Do not invent charges.",
        "published",
        "assistant-platform",
        List.of());
  }

  private static PromptPack feeExplainPrior() {
    return new PromptPack(
        "fee_explain",
        "2026.07.1",
        "You explain account fees. Use the fee lookup tool.",
        "published",
        "assistant-platform",
        List.of());
  }

  private static PromptPack researchDraft() {
    return new PromptPack(
        "research",
        "2026.08.1",
        "Draft research host. Not published.",
        "draft",
        "assistant-platform",
        List.of());
  }

  private static PromptPack feeExplainV0() {
    return new PromptPack(
        "fee_explain",
        "2026.04.1",
        "Look up why an account fee posted.",
        "deprecated",
        "assistant-platform",
        List.of());
  }

  private static PromptPack contractInvestigate() {
    return new PromptPack(
        "contract_investigate",
        "2026.08.1",
        "Investigate the document using only allowed tools. Prefer evidence over speculation. Stop when risk is assessed or budget is exhausted.",
        "published",
        "legal-agents",
        List.of());
  }

  private static PromptPack contractReview() {
    return new PromptPack(
        "contract_review",
        "2026.08.1",
        "You are counsel's contract-review worker. Stay inside the current stage. Inside Analyse you may choose among the stage allowlist. Do not invent stages.",
        "published",
        "legal-agents",
        List.of(
            new PromptRoleTemplate(
                "synthesis",
                "synthesize",
                "Draft the counsel memo from validated stage outputs only. Ground claims in retrieved clauses and playbook hits.")));
  }

  private static PromptPack kycOnboarding() {
    return new PromptPack(
        "kyc_onboarding",
        "2026.08.1",
        "Summarize KYC evidence for a human reviewer. Do not recommend activation. Do not skip stages.",
        "published",
        "kyc-ops",
        List.of());
  }

  private static PromptPack accountBalance() {
    return new PromptPack(
        "account_balance",
        "2026.08.1",
        "Answer cleared-balance questions. Use list_accounts only.",
        "published",
        "assistant-platform",
        List.of());
  }

  private static PromptPack accountStatement() {
    return new PromptPack(
        "account_statement",
        "2026.08.1",
        "Assemble a statement pack. Use list_accounts and list_transactions. Do not initiate payments.",
        "published",
        "assistant-platform",
        List.of());
  }

  private static PromptPack accountHistory() {
    return new PromptPack(
        "account_history",
        "2026.08.1",
        "Answer account and transaction history questions. Read-only tools only.",
        "published",
        "assistant-platform",
        List.of());
  }

  private static PromptPack payments() {
    return new PromptPack(
        "payments",
        "2026.08.1",
        "Help initiate an outbound payment. Do not skip validation.",
        "published",
        "payments-agents",
        List.of());
  }

  private static PromptPack policyQa() {
    return new PromptPack(
        "agent-policy-qa",
        "2026.08.1",
        "Answer from retrieved policy text only. Do not invent policy.",
        "published",
        "assistant-platform",
        List.of());
  }

  private static PromptPack chat() {
    return new PromptPack(
        "agent-chat",
        "2026.08.1",
        "Be a concise corporate assistant. No tools.",
        "published",
        "assistant-platform",
        List.of());
  }

  private static PromptPack escalate() {
    return new PromptPack(
        "escalate",
        "2026.08.1",
        "Hand the conversation to a human agent. Do not continue the task.",
        "published",
        "assistant-platform",
        List.of());
  }

  private void put(PromptPack pack) {
    rows.put(key(pack.promptId(), pack.promptVersion()), pack);
  }

  @Override
  public Optional<PromptPack> find(String promptId, String promptVersion) {
    return Optional.ofNullable(rows.get(key(promptId, promptVersion)));
  }

  @Override
  public Optional<PromptPack> findPublished(String promptId) {
    return rows.values().stream()
        .filter(pack -> pack.promptId().equals(promptId) && "published".equals(pack.status()))
        .max((a, b) -> CatalogVersion.compare(a.promptVersion(), b.promptVersion()));
  }

  @Override
  public List<PromptPack> listPublished() {
    Map<String, PromptPack> latest = new LinkedHashMap<>();
    for (PromptPack pack : rows.values()) {
      if (!"published".equals(pack.status())) {
        continue;
      }
      PromptPack existing = latest.get(pack.promptId());
      if (existing == null
          || CatalogVersion.compare(pack.promptVersion(), existing.promptVersion()) > 0) {
        latest.put(pack.promptId(), pack);
      }
    }
    return latest.values().stream().sorted(Comparator.comparing(PromptPack::promptId)).toList();
  }

  @Override
  public List<PromptPack> listAll() {
    return rows.values().stream()
        .sorted(
            Comparator.comparing(PromptPack::promptId)
                .thenComparing((a, b) -> CatalogVersion.compare(b.promptVersion(), a.promptVersion())))
        .toList();
  }

  @Override
  public List<PromptPack> listVersions(String promptId) {
    return rows.values().stream()
        .filter(pack -> pack.promptId().equals(promptId))
        .sorted((a, b) -> CatalogVersion.compare(b.promptVersion(), a.promptVersion()))
        .toList();
  }

  private static String key(String promptId, String promptVersion) {
    return promptId + "@" + promptVersion;
  }
}
