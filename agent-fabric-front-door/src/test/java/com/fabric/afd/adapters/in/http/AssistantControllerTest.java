package com.fabric.afd.adapters.in.http;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fabric.afd.application.AssistantService;
import com.fabric.afd.application.BusinessEvents;
import com.fabric.afd.application.CataloguePort;
import com.fabric.afd.application.DecidePort;
import com.fabric.afd.application.HealthService;
import com.fabric.afd.application.InMemoryFreezeStore;
import com.fabric.afd.application.RuntimePort;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.EligibleRoute;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.RunStart;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@WebMvcTest(controllers = {AssistantController.class, HealthController.class, ApiExceptionHandler.class})
@Import({RequestIdFilter.class, ChannelAuthFilter.class, AssistantControllerTest.MemConfig.class})
class AssistantControllerTest {

  private static final String JANE = "{\"sub\":\"jane\",\"emts\":{\"accounts:read\":true}}";
  private static final String[] FR5 = {
    "route_id", "run_id", "agent_client_id", "confidence", "router_layer"
  };

  @Autowired private MockMvc mvc;

  @Test
  void hintsReturnOpaqueChips() throws Exception {
    MvcResult result =
        mvc.perform(get("/v1/assistant/hints").header("Authorization", "Bearer stub").header("X-Stub-Claims", JANE))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.session_id").isString())
            .andExpect(jsonPath("$.hints[0].hint_id").isString())
            .andExpect(jsonPath("$.hints[0].label").value("Explain a fee"))
            .andReturn();
    assertFr5(result.getResponse().getContentAsString());
  }

  @Test
  void demoTurnThenEventsAreSlim() throws Exception {
    MvcResult accepted =
        mvc.perform(
                post("/v1/assistant/turns")
                    .header("Authorization", "Bearer stub")
                    .header("X-Stub-Claims", JANE)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(
                        """
                        {"session_id":"chat-11111111-1111-4111-8111-111111111111","message":"Why was I charged $42?","hint_id":null,"option_id":null}
                        """))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.session_id").value("chat-11111111-1111-4111-8111-111111111111"))
            .andExpect(jsonPath("$.status").value("accepted"))
            .andReturn();
    assertFr5(accepted.getResponse().getContentAsString());

    MvcResult events =
        mvc.perform(
                get("/v1/assistant/sessions/chat-11111111-1111-4111-8111-111111111111/events")
                    .header("Authorization", "Bearer stub")
                    .header("X-Stub-Claims", JANE))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("completed"))
            .andExpect(jsonPath("$.message").value("Fee of $42 is the monthly account charge."))
            .andReturn();
    assertFr5(events.getResponse().getContentAsString());
  }

  @Test
  void missingBearerIs401() throws Exception {
    mvc.perform(
            post("/v1/assistant/turns")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"message\":\"hi\"}"))
        .andExpect(status().isUnauthorized());
  }

  private static void assertFr5(String json) {
    for (String key : FR5) {
      org.assertj.core.api.Assertions.assertThat(json).doesNotContain("\"" + key + "\"");
    }
  }

  @TestConfiguration
  static class MemConfig {
    @Bean
    HealthService healthService() {
      return new HealthService();
    }

    @Bean
    AssistantService assistantService() {
      return new AssistantService(
          new StubDecide(),
          new StubCatalogue(),
          new StubRuntime(),
          new InMemoryFreezeStore(),
          new BusinessEvents(new SimpleMeterRegistry()));
    }
  }

  private static final class StubDecide implements DecidePort {
    @Override
    public DecideOutcome decide(DecideCall call) {
      return new DecideOutcome("route", "fee_explain", "2026.08.1");
    }
  }

  private static final class StubCatalogue implements CataloguePort {
    @Override
    public CatalogRoute get(String routeId, String routeVersion) {
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

  private static final class StubRuntime implements RuntimePort {
    @Override
    public String start(RunStart start) {
      return "corr-9f3c";
    }

    @Override
    public Map<String, Object> status(String correlationId, String activationTarget) {
      Map<String, Object> body = new LinkedHashMap<>();
      body.put("correlation_id", correlationId);
      body.put("status", "completed");
      body.put("result", Map.of("message", "Fee of $42 is the monthly account charge."));
      return body;
    }

    @Override
    public void resume(String correlationId, String message, String activationTarget) {}

    @Override
    public Map<String, Object> resumeTurn(
        String correlationId, Map<String, Object> body, String activationTarget) {
      return Map.of();
    }

    @Override
    public Optional<FrozenRoute> openRun(String sessionId) {
      return Optional.empty();
    }
  }
}
