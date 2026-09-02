package com.fabric.afd.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.EligibleRoute;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.NotFoundException;
import com.fabric.afd.domain.RunStart;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class AssistantServiceTest {

  private static final Set<String> FR5 =
      Set.of("route_id", "run_id", "agent_client_id", "confidence", "router_layer");

  private FakeDecide decide;
  private FakeCatalogue catalogue;
  private FakeRuntime runtime;
  private InMemoryFreezeStore freeze;
  private AssistantService assistant;

  @BeforeEach
  void setUp() {
    decide = new FakeDecide();
    catalogue = new FakeCatalogue();
    runtime = new FakeRuntime();
    freeze = new InMemoryFreezeStore();
    assistant = new AssistantService(decide, catalogue, runtime, freeze, new com.fabric.afd.application.BusinessEvents(new io.micrometer.core.instrument.simple.SimpleMeterRegistry()));
  }

  @Test
  void hintsMintsSessionAndReturnsOpaqueChipsOnly() {
    Map<String, Object> body = assistant.hints(null, jane());

    assertThat((String) body.get("session_id")).startsWith("chat-");
    @SuppressWarnings("unchecked")
    List<Map<String, Object>> hints = (List<Map<String, Object>>) body.get("hints");
    assertThat(hints).hasSize(1);
    assertThat(hints.getFirst().get("hint_id")).asString().startsWith("hint-");
    assertThat(hints.getFirst().get("label")).isEqualTo("Explain a fee");
    assertFr5(body);
    assertThat(freeze.resolveOpaque((String) body.get("session_id"), (String) hints.getFirst().get("hint_id")))
        .isEqualTo("fee_explain");
  }

  @Test
  void demoTurnFreezesAndStartsRuntime() {
    Map<String, Object> body =
        assistant.turn(null, "Why was I charged $42?", null, null, jane());

    assertThat(body.get("status")).isEqualTo("accepted");
    assertThat((String) body.get("session_id")).startsWith("chat-");
    assertFr5(body);
    assertThat(decide.calls).hasSize(1);
    DecideCall call = decide.calls.getFirst();
    assertThat(call.ingress()).isEqualTo("chat");
    assertThat(call.message()).isEqualTo("Why was I charged $42?");
    assertThat(call.routeId()).isNull();
    assertThat(runtime.starts).hasSize(1);
    FrozenRoute pin = freeze.get((String) body.get("session_id"));
    assertThat(pin.routeId()).isEqualTo("fee_explain");
    assertThat(pin.routeVersion()).isEqualTo("2026.08.1");
    assertThat(pin.activationTarget()).contains("/v1/runs");
    assertThat(pin.agentClientId()).isEqualTo("fee-explain-v1");
    assertThat(pin.correlationId()).isEqualTo("corr-9f3c");
  }

  @Test
  void hintTapIsLayerOneDecide() {
    Map<String, Object> hints = assistant.hints("chat-11111111-1111-4111-8111-111111111111", jane());
    @SuppressWarnings("unchecked")
    String hintId = (String) ((List<Map<String, Object>>) hints.get("hints")).getFirst().get("hint_id");

    Map<String, Object> body = assistant.turn("chat-11111111-1111-4111-8111-111111111111", null, hintId, null, jane());

    assertThat(body.get("status")).isEqualTo("accepted");
    assertThat(decide.calls.getFirst().routeId()).isEqualTo("fee_explain");
    assertFr5(body);
  }

  @Test
  void clarifyReturnsOpaqueOptionsAndDoesNotStart() {
    decide.outcome =
        new DecideOutcome(
            "clarify",
            null,
            null,
            "Did you want a fee explanation or recent transactions?",
            List.of(
                Map.of("intent_label", "fee_explain", "route_id", "fee_explain", "label", "Explain a fee")));

    Map<String, Object> body = assistant.turn("chat-11111111-1111-4111-8111-111111111111", "what about my account", null, null, jane());

    assertThat(body.get("status")).isEqualTo("clarify");
    assertThat(body.get("prompt")).asString().contains("fee explanation");
    @SuppressWarnings("unchecked")
    List<Map<String, Object>> options = (List<Map<String, Object>>) body.get("options");
    assertThat(options.getFirst().get("id")).asString().startsWith("opt-");
    assertThat(options.getFirst().get("label")).isEqualTo("Explain a fee");
    assertThat(runtime.starts).isEmpty();
    assertThat(freeze.get("chat-11111111-1111-4111-8111-111111111111")).isNull();
    assertFr5(body);
  }

  @Test
  void eventsPollsRuntimeWithoutDecide() {
    assistant.turn("chat-11111111-1111-4111-8111-111111111111", "Why was I charged $42?", null, null, jane());
    decide.calls.clear();
    catalogue.gets.clear();

    Map<String, Object> body = assistant.events("chat-11111111-1111-4111-8111-111111111111");

    assertThat(body.get("status")).isEqualTo("completed");
    assertThat(body.get("message")).isEqualTo("Fee of $42 is the monthly account charge.");
    assertThat(decide.calls).isEmpty();
    assertThat(catalogue.gets).isEmpty();
    assertThat(runtime.statusIds).containsExactly("corr-9f3c");
    assertFr5(body);
  }

  @Test
  void continuationSkipsDecideAndResumesRuntime() {
    runtime.statusValue = "waiting";
    assistant.turn("chat-11111111-1111-4111-8111-111111111111", "Why was I charged $42?", null, null, jane());
    Map<String, Object> again = assistant.turn("chat-11111111-1111-4111-8111-111111111111", "yes", null, null, jane());

    assertThat(again.get("status")).isEqualTo("accepted");
    assertThat(decide.calls).hasSize(1);
    assertThat(runtime.starts).hasSize(1);
    assertThat(runtime.resumes).containsExactly("corr-9f3c:yes");
    assertFr5(again);
  }

  @Test
  void completedRunStartsFreshInsteadOfResume() {
    runtime.statusValue = "completed";
    assistant.turn("chat-11111111-1111-4111-8111-111111111111", "Why was I charged $42?", null, null, jane());
    Map<String, Object> again = assistant.turn("chat-11111111-1111-4111-8111-111111111111", "another question", null, null, jane());

    assertThat(again.get("status")).isEqualTo("accepted");
    assertThat(decide.calls).hasSize(2);
    assertThat(runtime.starts).hasSize(2);
    assertThat(runtime.resumes).isEmpty();
  }

  @Test
  void freezeTtlMissRestoresFromRuntimeOpenRun() {
    runtime.statusValue = "waiting";
    assistant.turn("chat-11111111-1111-4111-8111-111111111111", "Why was I charged $42?", null, null, jane());
    freeze.expire("chat-11111111-1111-4111-8111-111111111111");
    runtime.open =
        Optional.of(
            new FrozenRoute(
                "chat-11111111-1111-4111-8111-111111111111",
                null,
                "fee_explain",
                "2026.08.1",
                "http://agent-runtime:3008/v1/runs",
                "fee-explain-v1",
                "corr-9f3c"));

    Map<String, Object> again = assistant.turn("chat-11111111-1111-4111-8111-111111111111", "yes", null, null, jane());

    assertThat(again.get("status")).isEqualTo("accepted");
    assertThat(decide.calls).hasSize(1);
    assertThat(runtime.starts).hasSize(1);
    assertThat(runtime.resumes).containsExactly("corr-9f3c:yes");
    assertThat(runtime.openLookups).contains("chat-11111111-1111-4111-8111-111111111111");
  }

  @Test
  void unknownSessionEventsAreNotFound() {
    assertThatThrownBy(() -> assistant.events("sess-missing")).isInstanceOf(NotFoundException.class);
  }

  private static void assertFr5(Object node) {
    if (node instanceof Map<?, ?> map) {
      for (var entry : map.entrySet()) {
        assertThat(String.valueOf(entry.getKey())).isNotIn(FR5);
        assertFr5(entry.getValue());
      }
    } else if (node instanceof List<?> list) {
      list.forEach(AssistantServiceTest::assertFr5);
    }
  }

  private static Map<String, Object> jane() {
    return Map.of("sub", "jane", "emts", Map.of("accounts:read", true));
  }

  private static final class FakeDecide implements DecidePort {
    final List<DecideCall> calls = new ArrayList<>();
    DecideOutcome outcome = new DecideOutcome("route", "fee_explain", "2026.08.1");

    @Override
    public DecideOutcome decide(DecideCall call) {
      calls.add(call);
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
      return List.of(new EligibleRoute("fee_explain", "2026.08.1", "fee_explain", "Explain a fee"));
    }
  }

  private static final class FakeRuntime implements RuntimePort {
    final List<RunStart> starts = new ArrayList<>();
    final List<String> statusIds = new ArrayList<>();
    final List<String> resumes = new ArrayList<>();
    final List<String> openLookups = new ArrayList<>();
    Optional<FrozenRoute> open = Optional.empty();
    String statusValue = "completed";

    @Override
    public String start(RunStart start) {
      starts.add(start);
      return "corr-9f3c";
    }

    @Override
    public Map<String, Object> status(String correlationId, String activationTarget) {
      statusIds.add(correlationId);
      Map<String, Object> body = new LinkedHashMap<>();
      body.put("correlation_id", correlationId);
      body.put("status", statusValue);
      body.put("result", Map.of("message", "Fee of $42 is the monthly account charge."));
      return body;
    }

    @Override
    public void resume(String correlationId, String message, String activationTarget) {
      resumes.add(correlationId + ":" + message);
    }

    @Override
    public Map<String, Object> resumeTurn(
        String correlationId, Map<String, Object> body, String activationTarget) {
      resume(correlationId, String.valueOf(body.get("message")), activationTarget);
      return Map.of("status", "completed");
    }

    @Override
    public Optional<FrozenRoute> openRun(String sessionId) {
      openLookups.add(sessionId);
      return open;
    }
  }
}
