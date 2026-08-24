package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.layers.ClassifierLayer;
import com.fabric.adp.application.layers.DecideLayer;
import com.fabric.adp.application.layers.LlmFallbackLayer;
import com.fabric.adp.application.layers.LlmFallbackPool;
import com.fabric.adp.application.layers.RulesLayer;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.ForbiddenException;
import com.fabric.adp.domain.RouteRow;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class DecideServiceTest {

  private DecideService decide;

  @BeforeEach
  void setUp() {
    decide =
        new DecideService(
            new CatalogueService(new InMemoryRouteStore().seedDemo()),
            new BusinessEvents(new SimpleMeterRegistry()),
            demoRules());
  }

  @Test
  void feeUtteranceRoutesToFeeExplain() {
    DecideResult result = decide.decide(chat("Why was I charged $42?", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("fee_explain");
    assertThat(result.routeVersion()).isEqualTo("2026.08.1");
    assertThat(result.confidence()).isEqualTo(0.91);
    assertLayer(result, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void emptyEligibleAbstains() {
    DecideResult result =
        decide.decide(
            new DecideRequest("chat", "sms", "s", "Why was I charged $42?", null, jane()), "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertLayer(result, null);
  }

  @Test
  void closeKeywordMatchClarifies() {
    DecideResult result = decide.decide(chat("hello", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("clarify");
    assertThat(result.candidates()).hasSize(2);
    assertLayer(result, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void hiInsideThisDoesNotClassifyChat() {
    DecideResult result =
        decide.decide(
            chat(
                "Start KYC onboarding for this applicant",
                Map.of("sub", "jane", "emts", Map.of("kyc:onboard", true))),
            "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertLayer(result, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void explicitRouteIdBindsWithoutKeywords() {
    DecideResult result =
        decide.decide(
            new DecideRequest("jobs", "web", "job:1", null, "fee_explain", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("fee_explain");
    assertThat(result.confidence()).isEqualTo(1.0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void jobsNamedHiddenRouteEntitlesWithoutChatVisible() {
    DecideResult result =
        decide.decide(
            new DecideRequest(
                "jobs",
                "web",
                "job:1",
                null,
                "claims_adjudicate",
                Map.of("sub", "jane", "emts", Map.of("claims:read", true))),
            "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("claims_adjudicate");
    assertThat(result.routeVersion()).isEqualTo("2026.08.1");
    assertThat(result.confidence()).isEqualTo(1.0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void jobsNamedHiddenRouteWithoutClaimAbstains() {
    DecideResult result =
        decide.decide(
            new DecideRequest("jobs", "web", "job:1", null, "claims_adjudicate", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertThat(result.outcome()).isNotEqualTo("clarify");
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void arCallerIsForbidden() {
    org.assertj.core.api.Assertions.assertThatThrownBy(
            () -> decide.decide(chat("Why was I charged $42?", jane()), "ar"))
        .isInstanceOf(ForbiddenException.class);
  }

  @Test
  void emptyEligibleAbstainsBeforeClassifier() {
    AtomicInteger classifierCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), new LlmFallbackLayer())
            .decide(
                new DecideRequest("chat", "sms", "s", "Why was I charged $42?", null, jane()),
                "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertThat(classifierCalls).hasValue(0);
    assertLayer(result, null);
  }

  @Test
  void chatHintRouteIdBindsFromEligibleAndSkipsClassifier() {
    AtomicInteger classifierCalls = new AtomicInteger();
    AtomicInteger llmCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), counting(llmCalls))
            .decide(
                new DecideRequest("chat", "web", "sess-88", "hello", "fee_explain", jane()),
                "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("fee_explain");
    assertThat(result.confidence()).isEqualTo(1.0);
    assertOneOnly(result, classifierCalls, llmCalls);
  }

  @Test
  void chatUnknownRouteIdAbstainsWithoutKeywordMatch() {
    AtomicInteger classifierCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), new LlmFallbackLayer())
            .decide(
                new DecideRequest(
                    "chat", "web", "sess-88", "Why was I charged $42?", "not_a_route", jane()),
                "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertThat(result.routeId()).isNull();
    assertThat(classifierCalls).hasValue(0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void jobsNamedRouteIdDoesNotEnterClassifierOrClarify() {
    AtomicInteger classifierCalls = new AtomicInteger();
    AtomicInteger llmCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), counting(llmCalls))
            .decide(
                new DecideRequest("jobs", "web", "job:1", "hello", "fee_explain", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("fee_explain");
    assertThat(result.confidence()).isEqualTo(1.0);
    assertOneOnly(result, classifierCalls, llmCalls);
  }

  @Test
  void jobsUnknownRouteIdAbstainsWithoutClarify() {
    AtomicInteger classifierCalls = new AtomicInteger();
    AtomicInteger llmCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), counting(llmCalls))
            .decide(
                new DecideRequest("jobs", "web", "job:1", "hello", "no_such_route", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertThat(result.routeId()).isNull();
    assertOneOnly(result, classifierCalls, llmCalls);
  }

  @Test
  void jobsUnentitledRouteIdDoesNotKeywordRoute() {
    AtomicInteger classifierCalls = new AtomicInteger();
    AtomicInteger llmCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), counting(llmCalls))
            .decide(
                new DecideRequest(
                    "jobs",
                    "web",
                    "job:1",
                    "Why was I charged $42?",
                    "claims_adjudicate",
                    jane()),
                "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertThat(result.routeId()).isNull();
    assertOneOnly(result, classifierCalls, llmCalls);
  }

  @Test
  void freeTextChatStillRetrievesOverEligible() {
    AtomicInteger classifierCalls = new AtomicInteger();
    DecideLayer classifier =
        (request, eligible) -> {
          classifierCalls.incrementAndGet();
          assertThat(eligible)
              .extracting(row -> row.routeId())
              .doesNotContain("claims_adjudicate");
          return new ClassifierLayer().apply(request, eligible);
        };
    DecideResult result =
        pipeline(classifier, new LlmFallbackLayer())
            .decide(chat("Why was I charged $42?", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("fee_explain");
    assertThat(classifierCalls).hasValue(1);
    assertLayer(result, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void slashHrRoutesViaRulesWithoutKeywords() {
    AtomicInteger classifierCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), new LlmFallbackLayer()).decide(chat("/hr", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("agent-chat");
    assertThat(result.confidence()).isEqualTo(1.0);
    assertThat(classifierCalls).hasValue(0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void talkToAHumanRoutesViaRules() {
    DecideResult result = decide.decide(chat("Talk to a human", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("agent-chat");
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void slashCommandNotEligibleAbstainsWithoutKeywordFallthrough() {
    AtomicInteger classifierCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), new LlmFallbackLayer())
            .decide(chat("/freeze", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertThat(result.routeId()).isNull();
    assertThat(classifierCalls).hasValue(0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  @Test
  void uniqueHighRiskRetrieveClarifiesInsteadOfSilentRoute() {
    InMemoryRouteStore store = new InMemoryRouteStore().seedDemo();
    store.replace(
        chatVisible(store.activeRoute("card_freeze").orElseThrow(), List.of("unused_keyword")));
    DecideService withFreeze =
        new DecideService(
            new CatalogueService(store),
            new BusinessEvents(new SimpleMeterRegistry()),
            demoRules());
    Map<String, Object> entitled =
        Map.of("sub", "jane", "emts", Map.of("accounts:read", true, "cards:freeze", true));

    DecideResult freezeHit = withFreeze.decide(chat("Please freeze this card", entitled), "afd");
    assertThat(freezeHit.outcome()).isEqualTo("clarify");
    assertThat(freezeHit.routeId()).isNull();
    assertThat(freezeHit.candidates()).extracting(c -> c.get("route_id")).containsExactly("card_freeze");
    assertLayer(freezeHit, DecideResult.LAYER_RETRIEVE);

    DecideResult feeHit = withFreeze.decide(chat("Why was I charged $42?", entitled), "afd");
    assertThat(feeHit.outcome()).isEqualTo("route");
    assertThat(feeHit.routeId()).isEqualTo("fee_explain");
    assertLayer(feeHit, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void overBudgetRetrieveShedsWithoutCallingLlm() {
    AtomicInteger llmCalls = new AtomicInteger();
    DecideLayer slow =
        (request, eligible) -> {
          try {
            Thread.sleep(20);
          } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
          }
          return new ClassifierLayer().apply(request, eligible);
        };
    DecideResult result =
        pipeline(slow, counting(llmCalls), 5)
            .decide(chat("Why was I charged $42?", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("abstain");
    assertThat(result.routeId()).isNull();
    assertThat(llmCalls).hasValue(0);
    assertLayer(result, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void overBudgetRetrieveWithFlagOnDoesNotSubmitToLlmPool() {
    AtomicInteger submits = new AtomicInteger();
    ExecutorService pool = countingSubmits(submits);
    DecideLayer slow =
        (request, eligible) -> {
          try {
            Thread.sleep(20);
          } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
          }
          return new ClassifierLayer().apply(request, eligible);
        };
    try {
      DecideResult result =
          pipeline(slow, counting(new AtomicInteger()), 5, true, pool, 500)
              .decide(chat("Why was I charged $42?", jane()), "afd");
      assertThat(result.outcome()).isEqualTo("abstain");
      assertThat(submits).hasValue(0);
      assertLayer(result, DecideResult.LAYER_RETRIEVE);
    } finally {
      pool.shutdownNow();
    }
  }

  @Test
  void flagOffDoesNotCallLlmOnFeeOrJobsOrOod() {
    AtomicInteger feeLlm = new AtomicInteger();
    DecideResult fee =
        pipeline(new ClassifierLayer(), counting(feeLlm))
            .decide(chat("Why was I charged $42?", jane()), "afd");
    assertThat(fee.outcome()).isEqualTo("route");
    assertThat(fee.routeId()).isEqualTo("fee_explain");
    assertThat(feeLlm).hasValue(0);

    AtomicInteger jobsLlm = new AtomicInteger();
    DecideResult jobs =
        pipeline(counting(new AtomicInteger()), counting(jobsLlm))
            .decide(new DecideRequest("jobs", "web", "job:1", null, "fee_explain", jane()), "afd");
    assertThat(jobs.outcome()).isEqualTo("route");
    assertThat(jobsLlm).hasValue(0);

    AtomicInteger oodLlm = new AtomicInteger();
    DecideResult ood =
        pipeline(counting(new AtomicInteger()), counting(oodLlm))
            .decide(chat("xyzzy-no-such-intent", jane()), "afd");
    assertThat(ood.outcome()).isEqualTo("abstain");
    assertThat(oodLlm).hasValue(0);
    assertLayer(ood, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void flagOnInvokesPortOnOodButStubDoesNotRoute() {
    AtomicInteger llmCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(new AtomicInteger()), counting(llmCalls), DecideService.LAYER_TWO_BUDGET_MS, true)
            .decide(chat("xyzzy-no-such-intent", jane()), "afd");
    assertThat(llmCalls).hasValue(1);
    assertThat(result.outcome()).isEqualTo("abstain");
    assertLayer(result, DecideResult.LAYER_RETRIEVE);
  }

  @Test
  void hungLlmTimesOutWithoutBlockingDecideBeyondDeadline() {
    DecideLayer hung =
        (request, eligible) -> {
          try {
            Thread.sleep(400);
          } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
          }
          return Optional.empty();
        };
    long timeoutMs = 40;
    ExecutorService pool = LlmFallbackPool.create();
    try {
      long started = System.nanoTime();
      DecideResult result =
          pipeline(
                  counting(new AtomicInteger()),
                  hung,
                  DecideService.LAYER_TWO_BUDGET_MS,
                  true,
                  pool,
                  timeoutMs)
              .decide(chat("xyzzy-no-such-intent", jane()), "afd");
      long elapsed = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started);
      assertThat(result.outcome()).isEqualTo("abstain");
      assertThat(result.routeId()).isNull();
      assertLayer(result, DecideResult.LAYER_LLM);
      assertThat(elapsed).isLessThan(250L);
    } finally {
      pool.shutdownNow();
    }
  }

  @Test
  void flagOffDoesNotSubmitToLlmPool() {
    AtomicInteger submits = new AtomicInteger();
    ExecutorService pool = countingSubmits(submits);
    try {
      DecideService feeSvc =
          pipeline(
              new ClassifierLayer(),
              counting(new AtomicInteger()),
              DecideService.LAYER_TWO_BUDGET_MS,
              false,
              pool,
              DecideService.LAYER_THREE_TIMEOUT_MS);
      assertThat(feeSvc.decide(chat("Why was I charged $42?", jane()), "afd").routeId())
          .isEqualTo("fee_explain");

      DecideService jobsSvc =
          pipeline(
              counting(new AtomicInteger()),
              counting(new AtomicInteger()),
              DecideService.LAYER_TWO_BUDGET_MS,
              false,
              pool,
              DecideService.LAYER_THREE_TIMEOUT_MS);
      assertThat(
              jobsSvc
                  .decide(
                      new DecideRequest("jobs", "web", "job:1", null, "fee_explain", jane()), "afd")
                  .outcome())
          .isEqualTo("route");

      DecideService oodSvc =
          pipeline(
              counting(new AtomicInteger()),
              counting(new AtomicInteger()),
              DecideService.LAYER_TWO_BUDGET_MS,
              false,
              pool,
              DecideService.LAYER_THREE_TIMEOUT_MS);
      assertThat(oodSvc.decide(chat("xyzzy-no-such-intent", jane()), "afd").outcome())
          .isEqualTo("abstain");
      assertThat(submits).hasValue(0);
    } finally {
      pool.shutdownNow();
    }
  }

  @Test
  void jobsWithFlagOnDoesNotSubmitToLlmPool() {
    AtomicInteger submits = new AtomicInteger();
    ExecutorService pool = countingSubmits(submits);
    try {
      DecideResult result =
          pipeline(
                  counting(new AtomicInteger()),
                  counting(new AtomicInteger()),
                  DecideService.LAYER_TWO_BUDGET_MS,
                  true,
                  pool,
                  DecideService.LAYER_THREE_TIMEOUT_MS)
              .decide(new DecideRequest("jobs", "web", "job:1", null, "fee_explain", jane()), "afd");
      assertThat(result.outcome()).isEqualTo("route");
      assertThat(submits).hasValue(0);
    } finally {
      pool.shutdownNow();
    }
  }

  @Test
  void jobsBodyDoesNotParseChatSlash() {
    AtomicInteger classifierCalls = new AtomicInteger();
    DecideResult result =
        pipeline(counting(classifierCalls), new LlmFallbackLayer())
            .decide(
                new DecideRequest("jobs", "web", "job:1", "/hr", "fee_explain", jane()), "afd");
    assertThat(result.outcome()).isEqualTo("route");
    assertThat(result.routeId()).isEqualTo("fee_explain");
    assertThat(classifierCalls).hasValue(0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  private static void assertLayer(DecideResult result, String layer) {
    assertThat(result.routerLayer()).isEqualTo(layer);
    assertThat(result.latencyMs()).isNotNull().isGreaterThanOrEqualTo(0L);
  }

  private static void assertOneOnly(
      DecideResult result, AtomicInteger classifierCalls, AtomicInteger llmCalls) {
    assertThat(result.outcome()).isNotEqualTo("clarify");
    assertThat(classifierCalls).hasValue(0);
    assertThat(llmCalls).hasValue(0);
    assertLayer(result, DecideResult.LAYER_RULES);
  }

  private static DecideService pipeline(DecideLayer classifier, DecideLayer llmFallback) {
    return pipeline(classifier, llmFallback, DecideService.LAYER_TWO_BUDGET_MS, false);
  }

  private static DecideService pipeline(
      DecideLayer classifier, DecideLayer llmFallback, long layerTwoBudgetMs) {
    return pipeline(classifier, llmFallback, layerTwoBudgetMs, false);
  }

  private static DecideService pipeline(
      DecideLayer classifier,
      DecideLayer llmFallback,
      long layerTwoBudgetMs,
      boolean llmEnabled) {
    return pipeline(
        classifier,
        llmFallback,
        layerTwoBudgetMs,
        llmEnabled,
        LlmFallbackPool.create(),
        DecideService.LAYER_THREE_TIMEOUT_MS);
  }

  private static DecideService pipeline(
      DecideLayer classifier,
      DecideLayer llmFallback,
      long layerTwoBudgetMs,
      boolean llmEnabled,
      ExecutorService llmPool,
      long llmTimeoutMs) {
    return new DecideService(
        new CatalogueService(new InMemoryRouteStore().seedDemo()),
        new BusinessEvents(new SimpleMeterRegistry()),
        new RulesLayer(demoRules()),
        classifier,
        llmFallback,
        layerTwoBudgetMs,
        llmEnabled,
        llmPool,
        llmTimeoutMs);
  }

  private static ExecutorService countingSubmits(AtomicInteger submits) {
    return new ThreadPoolExecutor(
        2,
        2,
        60,
        TimeUnit.SECONDS,
        new SynchronousQueue<>(),
        task -> {
          Thread thread = new Thread(task, "test-layer-3");
          thread.setDaemon(true);
          return thread;
        },
        new ThreadPoolExecutor.AbortPolicy()) {
      @Override
      public <T> Future<T> submit(Callable<T> task) {
        submits.incrementAndGet();
        return super.submit(task);
      }
    };
  }

  private static IntentRuleStore demoRules() {
    return new InMemoryIntentRuleStore().seedDemo();
  }

  private static DecideLayer counting(AtomicInteger calls) {
    return (request, eligible) -> {
      calls.incrementAndGet();
      return Optional.empty();
    };
  }

  private static DecideRequest chat(String message, Map<String, Object> claims) {
    return new DecideRequest("chat", "web", "sess-88", message, null, claims);
  }

  private static RouteRow chatVisible(RouteRow row, List<String> keywords) {
    return new RouteRow(
        row.routeId(),
        row.routeVersion(),
        row.active(),
        row.intentLabel(),
        row.description(),
        row.activationTarget(),
        row.agentClientId(),
        row.manifest(),
        row.policyProfile(),
        row.modelProfile(),
        row.retrieval(),
        row.memoryProfile(),
        row.workflowId(),
        row.promptId(),
        row.outputSchemaId(),
        row.evalSuiteId(),
        row.maxLoopSteps(),
        row.fallback(),
        row.requiredClaims(),
        List.of("web"),
        true,
        keywords,
        row.autonomyMode());
  }

  private static Map<String, Object> jane() {
    return Map.of("sub", "jane", "emts", Map.of("accounts:read", true));
  }
}
