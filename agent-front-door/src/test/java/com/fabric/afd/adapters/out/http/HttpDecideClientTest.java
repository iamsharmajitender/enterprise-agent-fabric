package com.fabric.afd.adapters.out.http;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.jsonPath;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

class HttpDecideClientTest {

  private MockRestServiceServer server;
  private HttpDecideClient client;

  @BeforeEach
  void setUp() {
    RestClient.Builder builder = RestClient.builder().baseUrl("http://adp");
    server = MockRestServiceServer.bindTo(builder).build();
    client =
        new HttpDecideClient(
            builder
                .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer fabric-internal")
                .defaultHeader("X-Workload", "afd")
                .build());
  }

  @Test
  void postsJobsIngressWithExplicitRouteId() {
    server
        .expect(requestTo("http://adp/v1/intent/decide"))
        .andExpect(method(HttpMethod.POST))
        .andExpect(header(HttpHeaders.AUTHORIZATION, "Bearer fabric-internal"))
        .andExpect(header("X-Workload", "afd"))
        .andExpect(jsonPath("$.ingress").value("jobs"))
        .andExpect(jsonPath("$.route_id").value("fee_explain"))
        .andExpect(jsonPath("$.message").doesNotExist())
        .andRespond(
            withSuccess(
                """
                {"outcome":"route","route_id":"fee_explain","route_version":"2026.08.1"}
                """,
                MediaType.APPLICATION_JSON));

    DecideOutcome outcome =
        client.decide(
            new DecideCall(
                "jobs",
                "web",
                "job:job-fee-explain:v1",
                null,
                "fee_explain",
                Map.of("sub", "jane")));

    assertThat(outcome.routed()).isTrue();
    assertThat(outcome.routeId()).isEqualTo("fee_explain");
    assertThat(outcome.routeVersion()).isEqualTo("2026.08.1");
    server.verify();
  }
}
