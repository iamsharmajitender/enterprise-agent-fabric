package com.fabric.adp.application;

import com.fabric.adp.application.layers.ClassifierLayer;
import com.fabric.adp.application.layers.DecideLayer;
import com.fabric.adp.application.layers.LlmFallbackLayer;
import com.fabric.adp.application.layers.LlmFallbackPool;
import com.fabric.adp.application.layers.RulesLayer;
import com.fabric.adp.bootstrap.TraceIds;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.ForbiddenException;
import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Orchestrates decide. Front Door ({@code afd}) is the only caller.
 *
 * <pre>
 *   eligible = prune catalogue by ingress / channel / claims
 *   ① rules       — named route_id (jobs, chip) or seeded chat command. First hit wins. Else next.
 *   ② classifier  — in-process kNN over labelled utterances; risk bars apply.
 *                    Budget {@link #LAYER_TWO_BUDGET_MS} ms; over budget sheds (no ③).
 *   ③ llm         — default off. When on: bounded pool + timeout; shed → abstain, router_layer=llm.
 *   else abstain
 * </pre>
 *
 * A layer that returns a result stops the chain. Empty optional means "not me."
 */
public class DecideService {

  /** Layer ② must finish in less than this many milliseconds. At or over budget → shed, skip ③. */
  public static final long LAYER_TWO_BUDGET_MS = 50;

  /** Layer ③ HTTP/stub must finish in less than this many milliseconds. At or over → shed. */
  public static final long LAYER_THREE_TIMEOUT_MS = 500;

  /** Layer ③ stays off until I12. When false, decide never submits to the Layer ③ pool. */
  public static final boolean LLM_FALLBACK_DEFAULT = false;

  private final CatalogueService catalogue;
  private final BusinessEvents events;
  private final DecideLayer rules;
  private final DecideLayer classifier;
  private final DecideLayer llmFallback;
  private final long layerTwoBudgetMs;
  private final boolean llmEnabled;
  private final ExecutorService llmPool;
  private final long llmTimeoutMs;
  private final AuditPort audit;

  public DecideService(CatalogueService catalogue, BusinessEvents events) {
    this(catalogue, events, () -> List.of());
  }

  public DecideService(CatalogueService catalogue, BusinessEvents events, IntentRuleStore rules) {
    this(catalogue, events, rules, LLM_FALLBACK_DEFAULT);
  }

  public DecideService(
      CatalogueService catalogue,
      BusinessEvents events,
      IntentRuleStore rules,
      boolean llmEnabled) {
    this(catalogue, events, rules, llmEnabled, LlmFallbackPool.create(), LAYER_THREE_TIMEOUT_MS);
  }

  public DecideService(
      CatalogueService catalogue,
      BusinessEvents events,
      IntentRuleStore rules,
      boolean llmEnabled,
      ExecutorService llmPool,
      long llmTimeoutMs) {
    this(catalogue, events, rules, llmEnabled, llmPool, llmTimeoutMs, AuditPort.NOOP);
  }

  public DecideService(
      CatalogueService catalogue,
      BusinessEvents events,
      IntentRuleStore rules,
      boolean llmEnabled,
      ExecutorService llmPool,
      long llmTimeoutMs,
      AuditPort audit) {
    this(
        catalogue,
        events,
        new RulesLayer(rules),
        new ClassifierLayer(),
        new LlmFallbackLayer(llmEnabled),
        LAYER_TWO_BUDGET_MS,
        llmEnabled,
        llmPool,
        llmTimeoutMs,
        audit);
  }

  DecideService(
      CatalogueService catalogue,
      BusinessEvents events,
      DecideLayer rules,
      DecideLayer classifier,
      DecideLayer llmFallback) {
    this(catalogue, events, rules, classifier, llmFallback, LAYER_TWO_BUDGET_MS, LLM_FALLBACK_DEFAULT);
  }

  DecideService(
      CatalogueService catalogue,
      BusinessEvents events,
      DecideLayer rules,
      DecideLayer classifier,
      DecideLayer llmFallback,
      long layerTwoBudgetMs) {
    this(catalogue, events, rules, classifier, llmFallback, layerTwoBudgetMs, LLM_FALLBACK_DEFAULT);
  }

  DecideService(
      CatalogueService catalogue,
      BusinessEvents events,
      DecideLayer rules,
      DecideLayer classifier,
      DecideLayer llmFallback,
      long layerTwoBudgetMs,
      boolean llmEnabled) {
    this(
        catalogue,
        events,
        rules,
        classifier,
        llmFallback,
        layerTwoBudgetMs,
        llmEnabled,
        LlmFallbackPool.create(),
        LAYER_THREE_TIMEOUT_MS);
  }

  DecideService(
      CatalogueService catalogue,
      BusinessEvents events,
      DecideLayer rules,
      DecideLayer classifier,
      DecideLayer llmFallback,
      long layerTwoBudgetMs,
      boolean llmEnabled,
      ExecutorService llmPool,
      long llmTimeoutMs) {
    this(
        catalogue,
        events,
        rules,
        classifier,
        llmFallback,
        layerTwoBudgetMs,
        llmEnabled,
        llmPool,
        llmTimeoutMs,
        AuditPort.NOOP);
  }

  DecideService(
      CatalogueService catalogue,
      BusinessEvents events,
      DecideLayer rules,
      DecideLayer classifier,
      DecideLayer llmFallback,
      long layerTwoBudgetMs,
      boolean llmEnabled,
      ExecutorService llmPool,
      long llmTimeoutMs,
      AuditPort audit) {
    this.catalogue = catalogue;
    this.events = events;
    this.rules = rules;
    this.classifier = classifier;
    this.llmFallback = llmFallback;
    this.layerTwoBudgetMs = layerTwoBudgetMs;
    this.llmEnabled = llmEnabled;
    this.llmPool = llmPool;
    this.llmTimeoutMs = llmTimeoutMs;
    this.audit = audit == null ? AuditPort.NOOP : audit;
  }

  public DecideResult decide(DecideRequest request, String workload) {
    if (!"afd".equals(workload)) {
      throw new ForbiddenException("only afd may call decide");
    }
    long started = System.nanoTime();
    DecideResult result =
        resolve(request)
            .withLatencyMs(TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started));
    emitDecide(request, result);
    TraceIds.put("session_id", request.sessionId());
    TraceIds.put("outcome", result.outcome());
    TraceIds.put("route_id", result.routeId());
    TraceIds.put("route_version", result.routeVersion());
    TraceIds.put("router_layer", result.routerLayer());
    if (result.latencyMs() != null) {
      TraceIds.put("latency_ms", Long.toString(result.latencyMs()));
    }
    return result;
  }

  private DecideResult resolve(DecideRequest request) {
    List<RouteRow> eligible = pruneEligible(request);

    Optional<DecideResult> decided = tagged(DecideResult.LAYER_RULES, rules.apply(request, eligible));
    if (decided.isPresent()) {
      return decided.get();
    }

    // Named route_id (jobs / chat chip) stops at ①. Never keyword-match, never clarify.
    if (request.hasRouteId()) {
      return DecideResult.abstain(routeIds(eligible)).withRouterLayer(DecideResult.LAYER_RULES);
    }

    if (eligible.isEmpty()) {
      // No layer contested — omit router_layer.
      return DecideResult.abstain(List.of());
    }

    long retrieveStarted = System.nanoTime();
    Optional<DecideResult> retrieved = classifier.apply(request, eligible);
    long retrieveMs = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - retrieveStarted);
    if (retrieveMs >= layerTwoBudgetMs) {
      // Slow ② does not get a second chance at ③.
      return DecideResult.abstain(routeIds(eligible)).withRouterLayer(DecideResult.LAYER_RETRIEVE);
    }

    decided = tagged(DecideResult.LAYER_RETRIEVE, retrieved);
    if (decided.isPresent()) {
      return decided.get();
    }

    if (llmEnabled) {
      decided =
          tagged(
              DecideResult.LAYER_LLM,
              LlmFallbackPool.invoke(
                  llmPool,
                  llmTimeoutMs,
                  () -> llmFallback.apply(request, eligible),
                  routeIds(eligible)));
      if (decided.isPresent()) {
        return decided.get();
      }
    }

    return DecideResult.abstain(routeIds(eligible)).withRouterLayer(DecideResult.LAYER_RETRIEVE);
  }

  /**
   * Layer 0 — eligible set. Jobs + named id: every active row Jane is entitled to (hidden ok).
   * Chat: chat-visible ∩ channel ∩ claims.
   */
  private List<RouteRow> pruneEligible(DecideRequest request) {
    if ("jobs".equals(request.ingress()) && request.hasRouteId()) {
      return catalogue.list().stream()
          .filter(row -> request.entitledClaims().containsAll(row.requiredClaims()))
          .toList();
    }
    return catalogue.eligible(request.channel(), request.entitledClaims());
  }

  private static List<String> routeIds(List<RouteRow> rows) {
    return rows.stream().map(RouteRow::routeId).toList();
  }

  private void emitDecide(DecideRequest request, DecideResult result) {
    String prefix = "jobs".equals(request.ingress()) ? "job" : "chat";
    String journeyId =
        result.routeId() != null ? prefix + "." + result.routeId() : prefix + ".decide";
    String event =
        switch (result.outcome()) {
          case "route" -> prefix + ".intent.routed";
          case "clarify" -> prefix + ".intent.clarified";
          default -> prefix + ".intent.abstained";
        };
    events.emit(
        event,
        journeyId,
        BusinessEvents.fields(
            "outcome",
            result.outcome(),
            "route_id",
            result.routeId(),
            "route_version",
            result.routeVersion(),
            "session_id",
            request.sessionId(),
            "channel",
            request.channel(),
            "ingress",
            request.ingress(),
            "eligible_count",
            String.valueOf(result.eligibleRoutes() == null ? 0 : result.eligibleRoutes().size()),
            "router_layer",
            result.routerLayer(),
            "latency_ms",
            result.latencyMs() == null ? null : Long.toString(result.latencyMs())));
    events.countDecide(journeyId, result.outcome(), request.channel());
    String decisionId = "dec-" + java.util.UUID.randomUUID();
    audit.emitAsync(
        AuditEvents.decide(
            decisionId,
            request.sessionId(),
            result.outcome(),
            result.routeId(),
            result.routeVersion(),
            result.eligibleRoutes(),
            result.routerLayer(),
            AuditEvents.sha256Hex(String.valueOf(request.claims())),
            AuditEvents.sha256Hex(request.message()),
            request.channel(),
            request.ingress()));
  }

  private static Optional<DecideResult> tagged(String layer, Optional<DecideResult> decided) {
    return decided.map(result -> result.withRouterLayer(layer));
  }
}
