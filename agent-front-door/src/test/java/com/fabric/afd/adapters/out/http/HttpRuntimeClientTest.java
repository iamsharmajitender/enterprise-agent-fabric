package com.fabric.afd.adapters.out.http;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withResourceNotFound;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.HydrateFailedException;
import com.fabric.afd.domain.NotFoundException;
import com.fabric.afd.domain.RunStart;
import com.fabric.afd.domain.UnavailableException;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.test.web.client.response.MockRestResponseCreators;
import org.springframework.web.client.RestClient;

class HttpRuntimeClientTest {

  private MockRestServiceServer server;
  private HttpRuntimeClient client;

  @BeforeEach
  void setUp() {
    RestClient.Builder builder = RestClient.builder().baseUrl("http://ar");
    server = MockRestServiceServer.bindTo(builder).build();
    client = new HttpRuntimeClient(builder.build());
  }

  @Test
  void startPostsNewRunAndReadsCorrelationId() {
    server
        .expect(requestTo("http://ar/v1/runs"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(
            MockRestResponseCreators.withStatus(HttpStatus.ACCEPTED)
                .contentType(MediaType.APPLICATION_JSON)
                .body("{\"correlation_id\":\"corr-9f3c\"}"));

    String id =
        client.start(
            new RunStart(
                "job-fee-explain:v1",
                "job:job-fee-explain:v1",
                new CatalogRoute(
                    "fee_explain",
                    "2026.08.1",
                    "http://agent-runtime:3008/v1/runs",
                    "fee-explain-v1",
                    "fee_explain_v1",
                    "2026.08.1",
                    "accounts_read",
                    "stub",
                    12),
                Map.of("account_id", "acc-42")));

    assertThat(id).isEqualTo("corr-9f3c");
    server.verify();
  }

  @Test
  void statusReturnsSlimBody() {
    server
        .expect(requestTo("http://ar/v1/runs/corr-9f3c"))
        .andExpect(method(HttpMethod.GET))
        .andRespond(
            withSuccess(
                """
                {"correlation_id":"corr-9f3c","status":"completed","result":{"message":"Fee of $42 is the monthly account charge."}}
                """,
                MediaType.APPLICATION_JSON));

    Map<String, Object> body = client.status("corr-9f3c");
    assertThat(body.get("status")).isEqualTo("completed");
    server.verify();
  }

  @Test
  void missingRunIsNotFound() {
    server
        .expect(requestTo("http://ar/v1/runs/missing"))
        .andExpect(method(HttpMethod.GET))
        .andRespond(withResourceNotFound());

    assertThatThrownBy(() -> client.status("missing")).isInstanceOf(NotFoundException.class);
    server.verify();
  }

  @Test
  void resumePostsTurnOnExistingRun() {
    server
        .expect(requestTo("http://ar/v1/runs/corr-9f3c/turns"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(MockRestResponseCreators.withSuccess());

    client.resume("corr-9f3c", "yes");
    server.verify();
  }

  @Test
  void openRunReadsPinBySessionId() {
    server
        .expect(requestTo("http://ar/v1/runs?session_id=sess-88"))
        .andExpect(method(HttpMethod.GET))
        .andRespond(
            withSuccess(
                """
                {"correlation_id":"corr-9f3c","session_id":"sess-88","route_id":"fee_explain","route_version":"2026.08.1"}
                """,
                MediaType.APPLICATION_JSON));

    assertThat(client.openRun("sess-88").orElseThrow().correlationId()).isEqualTo("corr-9f3c");
    server.verify();
  }

  @Test
  void startHydrateFailedIsUnprocessable() {
    server
        .expect(requestTo("http://ar/v1/runs"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(
            MockRestResponseCreators.withStatus(HttpStatus.UNPROCESSABLE_ENTITY)
                .contentType(MediaType.APPLICATION_JSON)
                .body(
                    """
                    {"error":{"code":"HYDRATE_FAILED","message":"no manifest, workflow, or prompt on pinned catalogue row"}}
                    """));

    assertThatThrownBy(() -> client.start(feeExplainStart()))
        .isInstanceOf(HydrateFailedException.class)
        .hasMessage("no manifest, workflow, or prompt on pinned catalogue row");
    server.verify();
  }

  @Test
  void startServerErrorIsUnavailable() {
    server
        .expect(requestTo("http://ar/v1/runs"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(MockRestResponseCreators.withStatus(HttpStatus.SERVICE_UNAVAILABLE));

    assertThatThrownBy(() -> client.start(feeExplainStart())).isInstanceOf(UnavailableException.class);
    server.verify();
  }

  private static RunStart feeExplainStart() {
    return new RunStart(
        "job-fee-explain:v1",
        "job:job-fee-explain:v1",
        new CatalogRoute(
            "fee_explain",
            "2026.08.1",
            "http://agent-runtime:3008/v1/runs",
            "fee-explain-v1",
            "fee_explain_v1",
            "2026.08.1",
            "accounts_read",
            "stub",
            12),
        Map.of("account_id", "acc-42"));
  }
}
