package com.fabric.afd.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fabric.afd.domain.BadRequestException;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.EligibleRoute;
import com.fabric.afd.domain.ForbiddenException;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.HydrateFailedException;
import com.fabric.afd.domain.NotFoundException;
import com.fabric.afd.domain.RunStart;
import com.fabric.afd.domain.UnavailableException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class JobsServiceTest {

  private FakeDecide decide;
  private FakeCatalogue catalogue;
  private FakeRuntime runtime;
  private InMemoryFreezeStore freeze;
  private JobsService jobs;

  @BeforeEach
  void setUp() {
    decide = new FakeDecide();
    catalogue = new FakeCatalogue();
    runtime = new FakeRuntime();
    freeze = new InMemoryFreezeStore();
    jobs = new JobsService(decide, catalogue, runtime, freeze, new com.fabric.afd.application.BusinessEvents(new io.micrometer.core.instrument.simple.SimpleMeterRegistry()));
  }

  @Test
  void startRoutesThenFreezesAndStartsAr() {
    String correlationId = jobs.start("fee_explain", "job-fee-explain:v1", Map.of("account_id", "acc-42"), jane());

    assertThat(correlationId).isEqualTo("corr-9f3c");
    assertThat(decide.calls).hasSize(1);
    DecideCall call = decide.calls.getFirst();
    assertThat(call.ingress()).isEqualTo("jobs");
    assertThat(call.routeId()).isEqualTo("fee_explain");
    assertThat(call.message()).isNull();
    assertThat(call.channel()).isEqualTo("web");
    assertThat(runtime.starts).hasSize(1);
    assertThat(runtime.starts.getFirst().idempotencyKey()).isEqualTo("job-fee-explain:v1");
    String sessionId = runtime.starts.getFirst().sessionId();
    assertThat(sessionId).startsWith("job-");
    assertThat(sessionId).isEqualTo(com.fabric.afd.domain.SessionIds.mintJobOrSub("job-fee-explain:v1"));
    assertThat(freeze.get(sessionId).correlationId()).isEqualTo("corr-9f3c");
  }

  @Test
  void subagentIdempotencyMintsSubSession() {
    String correlationId =
        jobs.start("contract_review", "subagent-corr-parent-start_contract_review", Map.of(), jane());
    assertThat(correlationId).isEqualTo("corr-9f3c");
    String sessionId = runtime.starts.getFirst().sessionId();
    assertThat(sessionId).startsWith("sub-");
    assertThat(sessionId)
        .isEqualTo(
            com.fabric.afd.domain.SessionIds.mintJobOrSub(
                "subagent-corr-parent-start_contract_review"));
  }

  @Test
  void entitleMissDoesNotStartAr() {
    decide.outcome = new DecideOutcome("abstain", null, null);

    assertThatThrownBy(() -> jobs.start("fee_explain", "job-1", Map.of(), Map.of()))
        .isInstanceOf(ForbiddenException.class);
    assertThat(runtime.starts).isEmpty();
    assertThat(catalogue.gets).isEmpty();
  }

  @Test
  void clarifyDoesNotStartAr() {
    decide.outcome = new DecideOutcome("clarify", null, null);

    assertThatThrownBy(() -> jobs.start("fee_explain", "job-1", Map.of(), jane()))
        .isInstanceOf(ForbiddenException.class);
    assertThat(runtime.starts).isEmpty();
  }

  @Test
  void duplicateIdempotencyRetriesSameArStart() {
    jobs.start("fee_explain", "job-fee-explain:v1", Map.of(), jane());
    String again = jobs.start("fee_explain", "job-fee-explain:v1", Map.of(), jane());

    assertThat(again).isEqualTo("corr-9f3c");
    assertThat(runtime.starts).hasSize(2);
    assertThat(runtime.starts.get(0).idempotencyKey()).isEqualTo(runtime.starts.get(1).idempotencyKey());
    assertThat(runtime.starts.get(0).sessionId()).isEqualTo(runtime.starts.get(1).sessionId());
    assertThat(runtime.starts.get(0).sessionId()).startsWith("job-");
  }

  @Test
  void statusPollsRuntimeAndSkipsDecide() {
    Map<String, Object> body = jobs.status("corr-9f3c");

    assertThat(body.get("status")).isEqualTo("completed");
    assertThat(decide.calls).isEmpty();
    assertThat(runtime.statusIds).containsExactly("corr-9f3c");
  }

  @Test
  void unknownJobIsNotFound() {
    runtime.missing = true;
    assertThatThrownBy(() -> jobs.status("missing")).isInstanceOf(NotFoundException.class);
  }

  @Test
  void decideUnavailableIs503() {
    decide.fail = true;
    assertThatThrownBy(() -> jobs.start("fee_explain", "job-1", Map.of(), jane()))
        .isInstanceOf(UnavailableException.class);
    assertThat(runtime.starts).isEmpty();
  }

  @Test
  void runtimeHydrateFailedPropagates() {
    runtime.hydrateFail = true;
    assertThatThrownBy(() -> jobs.start("llm_pipeline", "job-1", Map.of(), jane()))
        .isInstanceOf(HydrateFailedException.class)
        .hasMessage("no manifest, workflow, or prompt on pinned catalogue row");
    assertThat(runtime.starts).isEmpty();
  }

  @Test
  void missingRouteIdIsBadRequest() {
    assertThatThrownBy(() -> jobs.start(" ", "job-1", Map.of(), jane()))
        .isInstanceOf(BadRequestException.class);
    assertThat(decide.calls).isEmpty();
  }

  private static Map<String, Object> jane() {
    return Map.of("sub", "jane", "emts", Map.of("accounts:read", true));
  }

  private static final class FakeDecide implements DecidePort {
    final List<DecideCall> calls = new ArrayList<>();
    DecideOutcome outcome = new DecideOutcome("route", "fee_explain", "2026.08.1");
    boolean fail;

    @Override
    public DecideOutcome decide(DecideCall call) {
      calls.add(call);
      if (fail) {
        throw new UnavailableException("decide unavailable");
      }
      return outcome;
    }
  }

  private static final class FakeCatalogue implements CataloguePort {
    final List<String> gets = new ArrayList<>();

    @Override
    public CatalogRoute get(String routeId, String routeVersion) {
      gets.add(routeId + "@" + routeVersion);
      return new CatalogRoute(
          routeId,
          routeVersion,
          "http://agent-runtime:3008/v1/runs",
          "fee-explain-v1",
          "fee_explain",
          "2026.08.1",
          "accounts_read",
          "stub",
          12);
    }

    @Override
    public List<EligibleRoute> eligible(String channel, Map<String, Object> claims) {
      return List.of();
    }
  }

  private static final class FakeRuntime implements RuntimePort {
    final List<RunStart> starts = new ArrayList<>();
    final List<String> statusIds = new ArrayList<>();
    boolean missing;
    boolean hydrateFail;

    @Override
    public String start(RunStart start) {
      if (hydrateFail) {
        throw new HydrateFailedException("no manifest, workflow, or prompt on pinned catalogue row");
      }
      starts.add(start);
      return "corr-9f3c";
    }

    @Override
    public Map<String, Object> status(String correlationId, String activationTarget) {
      statusIds.add(correlationId);
      if (missing) {
        throw new NotFoundException(correlationId);
      }
      Map<String, Object> body = new LinkedHashMap<>();
      body.put("correlation_id", correlationId);
      body.put("status", "completed");
      body.put("result", Map.of("message", "Fee of $42 is the monthly account charge."));
      return body;
    }

    @Override
    public void resume(String correlationId, String message, String activationTarget) {
      throw new UnsupportedOperationException("jobs do not resume");
    }

    @Override
    public Optional<FrozenRoute> openRun(String sessionId) {
      return Optional.empty();
    }
  }
}
