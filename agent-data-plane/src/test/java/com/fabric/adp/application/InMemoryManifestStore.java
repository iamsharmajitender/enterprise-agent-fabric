package com.fabric.adp.application;

import com.fabric.adp.adapters.out.jdbc.ManifestMapper;
import com.fabric.adp.domain.ToolManifest;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class InMemoryManifestStore implements ManifestStore {

  private static final ManifestMapper MAPPER = new ManifestMapper(new ObjectMapper());

  private final Map<String, ToolManifest> rows = new LinkedHashMap<>();

  public InMemoryManifestStore seedDemo() {
    put(searchOnly());
    put(researchAssistant());
    put(fraudOneTool());
    put(fraudCasefile());
    put(feeExplain());
    put(contractInvestigate());
    put(accountNotify());
    put(cardFreeze());
    put(disputeIntake());
    put(clauseLookup());
    put(templateRetrieve());
    put(msaRiskReview());
    put(kycOnboarding());
    put(claimsAdjudicate());
    put(ticketTriage());
    put(productExplain());
    put(narrowReview());
    put(contractReview());
    put(dueDiligence());
    put(packThenReview());
    return this;
  }

  public static ToolManifest feeExplain() {
    return parse(
        "fee_explain",
        "2026.08.1",
        "Look up why an account fee was charged",
        """
        [{"name":"account_fee_lookup","capability_id":"account_fee_lookup",
          "capability_version":"1.0.0","pdp_action":"account_fee_lookup","risk_tier":"low"}]
        """);
  }

  public static ToolManifest searchOnly() {
    return parse(
        "search_only",
        "2026.08.1",
        "One web search tool",
        """
        [{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0",
          "pdp_action":"web_search","risk_tier":"low"}]
        """);
  }

  public static ToolManifest researchAssistant() {
    return parse(
        "research_assistant",
        "2026.08.1",
        "Open research tools (no corpus retrieve)",
        """
        [{"name":"web_search","capability_id":"web_search","capability_version":"1.0.0","pdp_action":"web_search","risk_tier":"low"},
         {"name":"fetch_url","capability_id":"fetch_url","capability_version":"1.0.0","pdp_action":"fetch_url","risk_tier":"low"},
         {"name":"note_store","capability_id":"note_store","capability_version":"1.0.0","pdp_action":"note_store","risk_tier":"low"},
         {"name":"draft_brief","capability_id":"draft_brief","capability_version":"1.0.0","pdp_action":"draft_brief","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest fraudOneTool() {
    return parse(
        "fraud_one_tool",
        "2026.08.1",
        "Draft memo after prefetch",
        """
        [{"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0",
          "pdp_action":"draft_memo","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest fraudCasefile() {
    return parse(
        "fraud_casefile",
        "2026.08.1",
        "Non-retrieve fraud tools after prefetch",
        """
        [{"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
         {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
         {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest accountNotify() {
    return parse(
        "account_notify",
        "2026.08.1",
        "One notify tool",
        """
        [{"name":"notify_customer","capability_id":"notify_customer","capability_version":"1.0.0",
          "pdp_action":"notify_customer","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest cardFreeze() {
    return parse(
        "card_freeze",
        "2026.08.1",
        "Multi-tool card freeze write path",
        """
        [{"name":"identity_check","capability_id":"identity_check","capability_version":"1.0.0","pdp_action":"identity_check","risk_tier":"medium"},
         {"name":"limit_check","capability_id":"limit_check","capability_version":"1.0.0","pdp_action":"limit_check","risk_tier":"medium"},
         {"name":"freeze_card","capability_id":"freeze_card","capability_version":"1.0.0","pdp_action":"freeze_card","risk_tier":"high"}]
        """);
  }

  public static ToolManifest disputeIntake() {
    return parse(
        "dispute_intake",
        "2026.08.1",
        "Multi-tool dispute intake",
        """
        [{"name":"doc_intake","capability_id":"doc_intake","capability_version":"1.0.0","pdp_action":"doc_intake","risk_tier":"low"},
         {"name":"case_open","capability_id":"case_open","capability_version":"1.0.0","pdp_action":"case_open","risk_tier":"medium"},
         {"name":"packet_summarize","capability_id":"packet_summarize","capability_version":"1.0.0","pdp_action":"packet_summarize","risk_tier":"low"}]
        """);
  }

  public static ToolManifest clauseLookup() {
    return parse(
        "clause_lookup",
        "2026.08.1",
        "One named retrieve tool",
        """
        [{"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0",
          "pdp_action":"clause_search","risk_tier":"low"}]
        """);
  }

  public static ToolManifest templateRetrieve() {
    return parse(
        "template_retrieve",
        "2026.08.1",
        "Two retrieve tools plus score",
        """
        [{"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
         {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
         {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest claimsAdjudicate() {
    return parse(
        "claims_adjudicate",
        "2026.08.1",
        "Forced playbook retrieve then named clause retrieve",
        """
        [{"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
         {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
         {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
         {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest ticketTriage() {
    return parse(
        "ticket_triage",
        "2026.08.1",
        "Parser and scorer tools, no corpus retrieve",
        """
        [{"name":"parse_ticket","capability_id":"parse_ticket","capability_version":"1.0.0","pdp_action":"parse_ticket","risk_tier":"low"},
         {"name":"tag_intent","capability_id":"tag_intent","capability_version":"1.0.0","pdp_action":"tag_intent","risk_tier":"low"},
         {"name":"draft_reply","capability_id":"draft_reply","capability_version":"1.0.0","pdp_action":"draft_reply","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest productExplain() {
    return parse(
        "product_explain",
        "2026.08.1",
        "Non-retrieve analyse tools after prefetch",
        """
        [{"name":"score_offer","capability_id":"score_offer","capability_version":"1.0.0","pdp_action":"score_offer","risk_tier":"low"},
         {"name":"compare_options","capability_id":"compare_options","capability_version":"1.0.0","pdp_action":"compare_options","risk_tier":"low"}]
        """);
  }

  public static ToolManifest narrowReview() {
    return parse(
        "narrow_review",
        "2026.08.1",
        "Many tools, one retrieve tool in Analyse",
        """
        [{"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
         {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
         {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
         {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest dueDiligence() {
    return parse(
        "due_diligence",
        "2026.08.1",
        "Forced playbook retrieve then allowlisted retrieve",
        """
        [{"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0","pdp_action":"policy_search","risk_tier":"low"},
         {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0","pdp_action":"clause_search","risk_tier":"low"},
         {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
         {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest packThenReview() {
    return parse(
        "pack_then_review",
        "2026.08.1",
        "Tools after playbook prefetch",
        """
        [{"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0","pdp_action":"ocr_extract","risk_tier":"low"},
         {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0","pdp_action":"risk_engine","risk_tier":"medium"},
         {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0","pdp_action":"draft_memo","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest researchDraft() {
    return parse(
        "research_tools",
        "2026.08.1",
        "Draft research tools, not live",
        "[]",
        "draft");
  }

  public static ToolManifest faxLookupRetired() {
    return parse(
        "fax_lookup",
        "2026.04.1",
        "Retired fax lookup tools",
        "[]",
        "retired");
  }

  public static ToolManifest accountBalance() {
    return parse(
        "account-balance-v1",
        "2026.08.1",
        "List accounts to answer a cleared-balance question",
        """
        [{"name":"list_accounts","capability_id":"list_accounts","capability_version":"1.0.0",
          "pdp_action":"list_accounts","risk_tier":"low"}]
        """);
  }

  public static ToolManifest accountStatement() {
    return parse(
        "account-statement-v1",
        "2026.08.1",
        "List accounts and transactions for a statement pack",
        """
        [{"name":"list_accounts","capability_id":"list_accounts","capability_version":"1.0.0",
          "pdp_action":"list_accounts","risk_tier":"low"},
         {"name":"list_transactions","capability_id":"list_transactions","capability_version":"1.0.0",
          "pdp_action":"list_transactions","risk_tier":"low"}]
        """);
  }

  public static ToolManifest contractInvestigate() {
    return parse(
        "contract_investigate",
        "2026.08.1",
        "Contract investigation tools (read-only + memo draft)",
        LEGAL_REVIEW_TOOLS);
  }

  public static ToolManifest contractReview() {
    return parse(
        "contract_review",
        "2026.08.1",
        "Guided contract review: fixed outer stages, flexible tools in Analyse",
        LEGAL_REVIEW_TOOLS);
  }

  public static ToolManifest msaRiskReview() {
    return parse(
        "msa_risk_review",
        "2026.08.1",
        "Fixed MSA risk review tools",
        LEGAL_REVIEW_TOOLS);
  }

  public static ToolManifest kycOnboarding() {
    return parse(
        "kyc_onboarding",
        "2026.08.1",
        "KYC onboarding tools with gated account activation",
        """
        [{"name":"doc_intake","capability_id":"doc_intake","capability_version":"1.0.0",
          "pdp_action":"doc_intake","risk_tier":"low"},
         {"name":"id_verify","capability_id":"id_verify","capability_version":"1.0.0",
          "pdp_action":"id_verify","risk_tier":"medium"},
         {"name":"sanctions_api","capability_id":"sanctions_api","capability_version":"1.0.0",
          "pdp_action":"sanctions_screen","risk_tier":"high"},
         {"name":"kyc_risk_engine","capability_id":"kyc_risk_engine","capability_version":"1.0.0",
          "pdp_action":"kyc_risk_score","risk_tier":"medium"},
         {"name":"account_activate","capability_id":"account_activate","capability_version":"1.0.0",
          "pdp_action":"account_activate","risk_tier":"high"}]
        """);
  }

  private static final String LEGAL_REVIEW_TOOLS =
      """
      [{"name":"ocr_extract","capability_id":"ocr_extract","capability_version":"1.2.0",
        "pdp_action":"ocr_extract","risk_tier":"low"},
       {"name":"clause_search","capability_id":"clause_search","capability_version":"1.0.0",
        "pdp_action":"clause_search","risk_tier":"low"},
       {"name":"policy_search","capability_id":"policy_search","capability_version":"1.0.0",
        "pdp_action":"policy_search","risk_tier":"low"},
       {"name":"risk_engine","capability_id":"risk_engine","capability_version":"1.0.0",
        "pdp_action":"risk_engine","risk_tier":"medium"},
       {"name":"draft_memo","capability_id":"draft_memo","capability_version":"1.0.0",
        "pdp_action":"draft_memo","risk_tier":"medium"}]
      """;

  public static ToolManifest accountsReadonly() {
    return parse(
        "accounts-readonly-v2",
        "2026.08.1",
        "Read-only account and transaction lookup",
        """
        [{"name":"list_accounts","capability_id":"list_accounts","capability_version":"1.0.0",
          "pdp_action":"list_accounts","risk_tier":"low"},
         {"name":"list_transactions","capability_id":"list_transactions","capability_version":"1.0.0",
          "pdp_action":"list_transactions","risk_tier":"low"}]
        """);
  }

  public static ToolManifest paymentsReadwrite() {
    return parse(
        "payments-readwrite-v3",
        "2026.07.1",
        "Lookup, validate, and initiate outbound wires",
        """
        [{"name":"lookup_beneficiary","capability_id":"lookup_beneficiary","capability_version":"1.0.0",
          "pdp_action":"lookup_beneficiary","risk_tier":"low"},
         {"name":"validate_payment","capability_id":"validate_payment","capability_version":"1.0.0",
          "pdp_action":"validate_payment","risk_tier":"medium"},
         {"name":"initiate_wire","capability_id":"initiate_wire","capability_version":"1.0.0",
          "pdp_action":"initiate_wire","risk_tier":"high"}]
        """);
  }

  public static ToolManifest handoff() {
    return parse(
        "handoff-v1",
        "2026.08.1",
        "Hand off the conversation to a human agent",
        """
        [{"name":"escalate_to_human","capability_id":"escalate_to_human","capability_version":"1.0.0",
          "pdp_action":"escalate_to_human","risk_tier":"medium"}]
        """);
  }

  public static ToolManifest fraudInvestigate() {
    return parse(
        "fraud_investigate",
        "2026.08.1",
        "Fraud investigate: domain tools plus Legal start",
        """
        [
          {
            "name": "search_transactions",
            "capability_id": "search_transactions",
            "capability_version": "1.4.0",
            "pdp_action": "search_transactions",
            "risk_tier": "low"
          },
          {
            "name": "ocr_extract",
            "capability_id": "ocr_extract",
            "capability_version": "1.2.0",
            "pdp_action": "ocr_extract",
            "risk_tier": "low"
          },
          {
            "name": "start_contract_review",
            "capability_id": "start_contract_review",
            "capability_version": "1.0.0",
            "pdp_action": "start_contract_review",
            "risk_tier": "high"
          }
        ]
        """);
  }

  private static ToolManifest parse(
      String id, String version, String description, String toolsJson) {
    return parse(id, version, description, toolsJson, "published");
  }

  private static ToolManifest parse(
      String id, String version, String description, String toolsJson, String status) {
    return MAPPER.parse(id, version, description, toolsJson, status);
  }

  private void put(ToolManifest manifest) {
    rows.put(key(manifest.manifestId(), manifest.manifestVersion()), manifest);
  }

  @Override
  public Optional<ToolManifest> find(String manifestId, String manifestVersion) {
    return Optional.ofNullable(rows.get(key(manifestId, manifestVersion)));
  }

  @Override
  public List<ToolManifest> listLatest() {
    Map<String, ToolManifest> latest = new HashMap<>();
    for (ToolManifest row : rows.values()) {
      ToolManifest existing = latest.get(row.manifestId());
      if (existing == null
          || CatalogVersion.compare(row.manifestVersion(), existing.manifestVersion()) > 0) {
        latest.put(row.manifestId(), row);
      }
    }
    return latest.values().stream()
        .sorted(Comparator.comparing(ToolManifest::manifestId))
        .toList();
  }

  @Override
  public List<ToolManifest> listAll() {
    return rows.values().stream()
        .sorted(
            Comparator.comparing(ToolManifest::manifestId)
                .thenComparing(
                    (a, b) -> CatalogVersion.compare(b.manifestVersion(), a.manifestVersion())))
        .toList();
  }

  @Override
  public List<ToolManifest> listVersions(String manifestId) {
    return rows.values().stream()
        .filter(row -> row.manifestId().equals(manifestId))
        .sorted((a, b) -> CatalogVersion.compare(b.manifestVersion(), a.manifestVersion()))
        .toList();
  }

  private static String key(String manifestId, String manifestVersion) {
    return manifestId + "@" + manifestVersion;
  }
}
