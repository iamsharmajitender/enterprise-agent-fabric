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
    put(pack(
        "chat_session",
        "Pattern 0. One synthesis turn per message. Continue the conversation. No tools. Do not invent facts."));
    put(policyQa());
    put(pack(
        "policy_chat",
        "Pattern 0. One synthesis turn. Answer from prefetched policy chunks. Use session memory. No tools."));
    put(pack(
        "search_only",
        "Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use web_search before DONE when search can answer. Do not invent results."));
    put(pack(
        "research_assistant",
        "Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use allowed tools. Prefer primary sources. Do not invent tool results."));
    put(pack(
        "fraud_one_tool",
        "Pattern 1. Reply CALL <tool_id> or DONE <answer>. The case file is already in context. CALL draft_memo before DONE.",
        "fraud-ops"));
    put(pack(
        "fraud_casefile",
        "Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use OCR, risk, and draft tools. Do not invent tool results.",
        "fraud-ops"));
    put(pack(
        "fraud_investigate",
        "Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use OCR and memo tools. You may CALL start_contract_review. Do not invent tools.",
        "fraud-ops"));
    put(pack(
        "ops_start_kyc",
        "Pattern 1. Reply CALL <tool_id> or DONE <answer>. Parse the ticket. You may CALL start_kyc_onboarding. Do not invent tools.",
        "ops"));
    put(feeExplain());
    put(contractInvestigate());
    put(pack(
        "llm_pipeline",
        "Pattern 2. Do only the current stage. Do not choose the next stage. No tools.",
        role("classify", "classify", "Extract the requested fields from the input only."),
        role("synthesis", "synthesize", "Rewrite or format using the previous stage output only.")));
    put(pack(
        "policy_memo",
        "Pattern 2. Do only the current stage. Draft from prefetched policy only.",
        role("synthesis", "synthesize", "Draft the memo from prefetched chunks only. Cite chunk ids.")));
    put(pack(
        "account_notify",
        "Pattern 2. Confirm the notify from stage outputs only. Do not invent send status.",
        "ops",
        role("synthesis", "synthesize", "Write the user-facing confirm from the notify tool output only.")));
    put(pack(
        "card_freeze",
        "Pattern 2. Confirm the freeze from identity, limit, and freeze outputs only. Do not invent card state.",
        "ops",
        role("synthesis", "synthesize", "Write the user-facing confirm from identity, limit, and freeze outputs only.")));
    put(pack(
        "dispute_intake",
        "Pattern 2. Do only the current stage. Do not open extra cases.",
        "ops",
        role("synthesis", "synthesize", "Summarize the dispute packet for a human reviewer. Do not recommend a payout.")));
    put(pack(
        "pack_then_notify",
        "Pattern 2. Confirm the notify from stage outputs only. Prefetch chunks may be empty.",
        "ops",
        role("synthesis", "synthesize", "Write the user-facing confirm from the notify tool output only.")));
    put(pack(
        "pack_then_freeze",
        "Pattern 2. Confirm the freeze from stage outputs only. Prefetch chunks may be empty.",
        "ops",
        role("synthesis", "synthesize", "Write the user-facing confirm from freeze-path stage outputs only.")));
    put(pack(
        "pack_then_review",
        "Pattern 2. Do only the current stage. Draft the memo from packed playbook and stage outputs.",
        "legal-agents",
        role("synthesis", "synthesize", "Draft the memo from packed playbook and stage outputs only.")));
    put(pack(
        "clause_lookup",
        "Pattern 2. Do only the current stage. Do not invent clauses.",
        "legal-agents",
        role("query_formulation", "plan", "Write the clause-index query from the goal only."),
        role(
            "synthesis",
            "synthesize",
            "Explain the retrieved clause in plain language. Do not invent text that is not in notes.")));
    put(pack(
        "template_retrieve",
        "Pattern 2. Do only the current stage. Write the query for this stage corpus only, or synthesize from notes.",
        "legal-agents",
        role(
            "query_formulation",
            "plan",
            "Write the search query for this stage's corpus only. Do not pick a different index."),
        role(
            "synthesis",
            "synthesize",
            "Summarize retrieved clauses, playbook hits, and the score. Do not invent sources.")));
    put(msaRiskReview());
    put(kycOnboarding());
    put(pack(
        "claims_adjudicate",
        "Pattern 2. Do only the current stage. Do not reorder stages.",
        "claims-ops",
        role(
            "query_formulation",
            "plan",
            "Write the clause-index query. Do not skip the forced playbook retrieve."),
        role("synthesis", "synthesize", "Draft the claims memo from stage outputs only.")));
    put(pack(
        "ticket_triage",
        "Pattern 3. Do only the current stage. Draft the reply from parse and tag outputs. Do not invent stages.",
        "ops",
        role("synthesis", "synthesize", "Draft the customer reply from parse and tag outputs only.")));
    put(pack(
        "product_explain",
        "Pattern 3. Product terms may already be packed. Explain from score and compare outputs only.",
        "product",
        role(
            "synthesis",
            "synthesize",
            "Explain the offer from score and compare outputs only. Do not invent rates.")));
    put(pack(
        "narrow_review",
        "Pattern 3. Do only the current stage. Analyse may use clause_search and risk_engine only.",
        "legal-agents",
        role("synthesis", "synthesize", "Draft the memo from Analyse outputs only.")));
    put(contractReview());
    put(pack(
        "due_diligence",
        "Pattern 3. Extract always retrieves the playbook. Analyse may retrieve again. Do not invent stages.",
        "legal-agents",
        role("synthesis", "synthesize", "Draft the diligence memo from Extract and Analyse outputs only.")));
    return this;
  }

  private static PromptPack pack(String promptId, String host, PromptRoleTemplate... roles) {
    return pack(promptId, host, "assistant-platform", roles);
  }

  private static PromptPack pack(
      String promptId, String host, String owner, PromptRoleTemplate... roles) {
    return new PromptPack(promptId, "2026.08.1", host, "published", owner, List.of(roles));
  }

  private static PromptRoleTemplate role(String llmRole, String taskType, String text) {
    return new PromptRoleTemplate(llmRole, taskType, text);
  }

  public static PromptPack msaRiskReview() {
    return new PromptPack(
        "msa_risk_review",
        "2026.08.1",
        "Pattern 2. You are counsel's MSA risk-review worker. Do only the current stage. Do not invent tools.",
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
        "Pattern 0. One synthesis turn. Summarize this email for the banker. No tools. Return short bullets.",
        "published",
        "assistant-platform",
        List.of());
  }

  public static PromptPack feeExplain() {
    return new PromptPack(
        "fee_explain",
        "2026.08.1",
        "Pattern 1. Reply CALL <tool_id> or DONE <answer>. CALL account_fee_lookup before DONE. Do not invent charges. After a tool result, DONE with that output unless another tool is needed.",
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
        "Pattern 1. Reply CALL <tool_id> or DONE <answer>. Use only allowed tools. Prefer evidence. Do not invent tool results.",
        "published",
        "legal-agents",
        List.of());
  }

  private static PromptPack contractReview() {
    return new PromptPack(
        "contract_review",
        "2026.08.1",
        "Pattern 3. Stay inside the current stage. Analyse may choose among the stage allowlist. Do not invent stages.",
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
        "Pattern 2. Summarize KYC evidence for a human reviewer. Do not recommend activation.",
        "published",
        "kyc-ops",
        List.of(
            new PromptRoleTemplate(
                "synthesis",
                "synthesize",
                "Summarize KYC stage outputs for a human reviewer. Do not recommend activation.")));
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
        "Pattern 0. One synthesis turn. Answer from retrieved policy text only. Do not invent policy. Cite chunk ids.",
        "published",
        "assistant-platform",
        List.of());
  }

  private static PromptPack chat() {
    return new PromptPack(
        "agent-chat",
        "2026.08.1",
        "Pattern 0. One synthesis turn. Be a concise corporate assistant. No tools.",
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
