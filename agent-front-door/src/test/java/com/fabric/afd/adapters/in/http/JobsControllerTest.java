package com.fabric.afd.adapters.in.http;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fabric.afd.application.CataloguePort;
import com.fabric.afd.application.DecidePort;
import com.fabric.afd.application.HealthService;
import com.fabric.afd.application.InMemoryFreezeStore;
import com.fabric.afd.application.JobsService;
import com.fabric.afd.application.RuntimePort;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.EligibleRoute;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.NotFoundException;
import com.fabric.afd.domain.RunStart;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(controllers = {JobsController.class, HealthController.class, ApiExceptionHandler.class})
@Import({ChannelAuthFilter.class, JobsControllerTest.MemConfig.class})
class JobsControllerTest {

  private static final String JANE = "{\"sub\":\"jane\",\"emts\":{\"accounts:read\":true}}";

  @Autowired private MockMvc mvc;

  @Test
  void healthStaysOpen() throws Exception {
    mvc.perform(get("/health")).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("UP"));
  }

  @Test
  void missingBearerIs401() throws Exception {
    mvc.perform(post("/v1/jobs").contentType(MediaType.APPLICATION_JSON).content("{}"))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void startFeeExplainReturnsAccepted() throws Exception {
    mvc.perform(
            post("/v1/jobs")
                .header("Authorization", "Bearer stub")
                .header("X-Stub-Claims", JANE)
                .contentType(MediaType.APPLICATION_JSON)
                .content(
                    """
                    {"route_id":"fee_explain","idempotency_key":"job-fee-explain:v1","payload":{"account_id":"acc-42"}}
                    """))
        .andExpect(status().isAccepted())
        .andExpect(jsonPath("$.correlation_id").value("corr-9f3c"));
  }

  @Test
  void duplicateKeyReturnsSameCorrelationId() throws Exception {
    String body =
        """
        {"route_id":"fee_explain","idempotency_key":"job-dup:v1","payload":{}}
        """;
    mvc.perform(
            post("/v1/jobs")
                .header("Authorization", "Bearer stub")
                .header("X-Stub-Claims", JANE)
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
        .andExpect(status().isAccepted())
        .andExpect(jsonPath("$.correlation_id").value("corr-job-dup:v1"));
    mvc.perform(
            post("/v1/jobs")
                .header("Authorization", "Bearer stub")
                .header("X-Stub-Claims", JANE)
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
        .andExpect(status().isAccepted())
        .andExpect(jsonPath("$.correlation_id").value("corr-job-dup:v1"));
  }

  @Test
  void missingClaimsIsForbidden() throws Exception {
    mvc.perform(
            post("/v1/jobs")
                .header("Authorization", "Bearer stub")
                .header("X-Stub-Claims", "{\"sub\":\"nobody\",\"emts\":{}}")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"route_id\":\"fee_explain\",\"idempotency_key\":\"job-nope:v1\"}"))
        .andExpect(status().isForbidden());
  }

  @Test
  void getStatusPollsRuntime() throws Exception {
    mvc.perform(
            get("/v1/jobs/corr-9f3c")
                .header("Authorization", "Bearer stub")
                .header("X-Stub-Claims", JANE))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.status").value("completed"))
        .andExpect(jsonPath("$.result.message").value("Fee of $42 is the monthly account charge."));
  }

  @Test
  void unknownJobIs404() throws Exception {
    mvc.perform(
            get("/v1/jobs/missing")
                .header("Authorization", "Bearer stub")
                .header("X-Stub-Claims", JANE))
        .andExpect(status().isNotFound());
  }

  @TestConfiguration
  static class MemConfig {
    @Bean
    HealthService healthService() {
      return new HealthService();
    }

    @Bean
    JobsService jobsService() {
      return new JobsService(new StubDecide(), new StubCatalogue(), new StubRuntime(), new InMemoryFreezeStore());
    }
  }

  private static final class StubDecide implements DecidePort {
    @Override
    public DecideOutcome decide(DecideCall call) {
      Object emts = call.claims() == null ? null : call.claims().get("emts");
      boolean entitled =
          emts instanceof Map<?, ?> map && Boolean.TRUE.equals(map.get("accounts:read"));
      if (!entitled) {
        return new DecideOutcome("abstain", null, null);
      }
      return new DecideOutcome("route", call.routeId(), "2026.08.1");
    }
  }

  private static final class StubCatalogue implements CataloguePort {
    @Override
    public CatalogRoute get(String routeId, String routeVersion) {
      return new CatalogRoute(
          routeId, routeVersion, "http://agent-runtime:3008/v1/runs", "fee-explain-v1",
          "fee_explain", "2026.08.1", "accounts_read", "stub", 12);
    }

    @Override
    public List<EligibleRoute> eligible(String channel, Map<String, Object> claims) {
      return List.of();
    }
  }

  private static final class StubRuntime implements RuntimePort {
    private final Map<String, String> keys = new ConcurrentHashMap<>();

    @Override
    public String start(RunStart start) {
      return keys.computeIfAbsent(
          start.idempotencyKey(),
          k -> "job-fee-explain:v1".equals(k) ? "corr-9f3c" : "corr-" + k);
    }

    @Override
    public Map<String, Object> status(String correlationId) {
      if ("missing".equals(correlationId)) {
        throw new NotFoundException(correlationId);
      }
      Map<String, Object> body = new LinkedHashMap<>();
      body.put("correlation_id", correlationId);
      body.put("status", "completed");
      body.put("result", Map.of("message", "Fee of $42 is the monthly account charge."));
      return body;
    }

    @Override
    public void resume(String correlationId, String message) {
      throw new UnsupportedOperationException("jobs do not resume");
    }

    @Override
    public Optional<FrozenRoute> openRun(String sessionId) {
      return Optional.empty();
    }
  }
}
