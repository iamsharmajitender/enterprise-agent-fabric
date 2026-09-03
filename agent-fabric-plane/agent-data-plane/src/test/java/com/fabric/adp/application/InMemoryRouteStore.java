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
    add(
        "shopassist_case",
        1,
        "shopassist_case",
        "Pattern 1 (autonomous): ShopAssist front-line support. ASK for order id if missing, lookup order, then billing and policy domain APIs. Escalate when needed.",
        RUNS,
        InMemoryManifestStore.shopassistCase(),
        null,
        loopMemory("none", 24),
        "read_only_standard",
        ModelProfile.REASONING_STANDARD,
        null,
        "shopassist_case",
        null,
        null,
        12,
        "clarify",
        List.of("support:case"),
        List.of("web", "api"),
        true,
        List.of("damaged", "damage", "refund", "jacket", "charged twice", "duplicate charge", "ORD-77819"));
    return this;
  }

  /** Full stack-route board for CI evals (routing / jobs-entitle / pin / route-quality). */
  public InMemoryRouteStore seedEvalBoard() {
    seedDemo();
    add(
        "billing_assistant",
        1,
        "billing_assistant",
        "Pattern 1 (autonomous): LLM CALL/DONE loop — picks account_fee_lookup or lookup_order_by_order_id based on the customer question.",
        RUNS,
        InMemoryManifestStore.billingAssistant(),
        null,
        loopMemory("none", 24),
        "read_only_standard",
        ModelProfile.REASONING_STANDARD,
        null,
        "billing_assistant",
        null,
        null,
        8,
        "clarify",
        List.of("accounts:read", "support:case"),
        List.of("web", "api"),
        true,
        List.of("fee", "charged", "charge", "order", "ORD-", "acct-", "status", "delivery"));
    add(
        "duplicate_charge_review",
        2,
        "duplicate_charge_review",
        "Pattern 2 (deterministic): classify order id, lookup order, duplicate-charge check with customer_id from lookup slot, synthesis reply.",
        RUNS,
        InMemoryManifestStore.duplicateChargeReview(),
        null,
        loopMemory("none", 24),
        "read_only_standard",
        ModelProfile.REASONING_STANDARD,
        "duplicate_charge_review",
        "duplicate_charge_review",
        null,
        "duplicate_charge_review_tools",
        null,
        "clarify",
        List.of("support:case"),
        List.of("web", "api"),
        true,
        List.of("charged twice", "duplicate charge", "double charge", "ORD-77819", "twice on order"));
    add(
        "fee_explain",
        1,
        "fee_explain",
        "Pattern 1 (autonomous): LLM CALL/DONE loop over account_fee_lookup. Domain HTTP only on CALL. No workflow.",
        RUNS,
        InMemoryManifestStore.feeExplain(),
        Retrieval.fromMode("tool", List.of("accounts")),
        loopMemory("none", 24),
        "read_only_standard",
        ModelProfile.REASONING_STANDARD,
        null,
        "fee_explain",
        null,
        null,
        6,
        "clarify",
        List.of("accounts:read"),
        List.of("web", "api"),
        true,
        List.of("fee", "charged", "charge", "42", "monthly", "why was i charged"));
    add(
        "kyc_onboarding",
        2,
        "kyc_onboarding",
        "Pattern 2 (deterministic): KYC pipeline with designer-owned branch on risk_score slot.",
        RUNS,
        InMemoryManifestStore.kycOnboarding(),
        null,
        loopMemory("none", 24),
        "read_only_standard",
        ModelProfile.REASONING_STANDARD,
        "kyc_onboarding",
        "kyc_onboarding",
        null,
        "kyc_onboarding_tools",
        null,
        "clarify",
        List.of("kyc:operate"),
        List.of("api"),
        false,
        List.of("kyc", "onboarding", "activate", "manual review", "applicant"));
    add(
        "overdraft_fee_qa",
        0,
        "overdraft_fee_qa",
        "Pattern 0 (single inference): one LLM call after catalogue prefetch of fee-schedule and product-disclosure.",
        RUNS,
        null,
        Retrieval.fromMode("deterministic_prefetch", List.of("fee-schedule", "product-disclosure")),
        null,
        "read_only_standard",
        ModelProfile.FAST_CHAT,
        null,
        "overdraft_fee_qa",
        null,
        null,
        1,
        "clarify",
        List.of(),
        List.of("web", "api"),
        true,
        List.of("overdraft", "fee", "everyday", "business", "corporate", "student", "premier"));
    add(
        "ticket_draft_reply",
        0,
        "ticket_draft_reply",
        "Pattern 0 child agent: draft customer reply from triage payload projected by parent ticket_triage.",
        RUNS,
        null,
        null,
        null,
        "read_only_standard",
        ModelProfile.FAST_CHAT,
        null,
        "ticket_draft_reply",
        null,
        null,
        1,
        "clarify",
        List.of("support:case"),
        List.of("api"),
        false,
        List.of());
    add(
        "ticket_triage",
        3,
        "ticket_triage",
        "Pattern 3 (guided): fixed outer stages parse → tag → draft_reply.",
        RUNS,
        InMemoryManifestStore.ticketTriage(),
        null,
        loopMemory("none", 24),
        "read_only_standard",
        ModelProfile.REASONING_STANDARD,
        "ticket_triage",
        "ticket_triage",
        null,
        "ticket_triage_tools",
        null,
        "clarify",
        List.of("support:case"),
        List.of("web", "api"),
        true,
        List.of("ticket", "triage", "duplicate charge", "billing", "ORD-77819", "support"));
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
