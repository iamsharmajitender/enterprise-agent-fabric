package com.fabric.afd.bootstrap;

import com.fabric.afd.adapters.out.http.HttpAuditClient;
import com.fabric.afd.adapters.out.http.HttpCatalogueClient;
import com.fabric.afd.adapters.out.http.HttpDecideClient;
import com.fabric.afd.adapters.out.http.HttpRuntimeClient;
import com.fabric.afd.adapters.out.http.RequestIdInterceptor;
import com.fabric.afd.adapters.out.jdbc.JdbcFreezeStore;
import com.fabric.afd.application.AssistantService;
import com.fabric.afd.application.AuditPort;
import com.fabric.afd.application.BusinessEvents;
import com.fabric.afd.application.CataloguePort;
import com.fabric.afd.application.DecidePort;
import com.fabric.afd.application.FreezeStore;
import com.fabric.afd.application.HealthService;
import com.fabric.afd.application.JobsService;
import com.fabric.afd.application.RuntimePort;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.MeterRegistry;
import java.net.http.HttpClient;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.web.client.RestClient;

@Configuration
public class FrontDoorConfig {

  @Bean
  HealthService healthService() {
    return new HealthService();
  }

  @Bean
  BusinessEvents businessEvents(MeterRegistry meters) {
    return new BusinessEvents(meters);
  }

  @Bean
  DecidePort decidePort(RestClient.Builder builder, @Value("${fabric.data-plane-url}") String baseUrl) {
    return new HttpDecideClient(workloadClient(builder, baseUrl, Duration.ofSeconds(30)));
  }

  @Bean
  CataloguePort cataloguePort(
      RestClient.Builder builder,
      @Value("${fabric.data-plane-url}") String baseUrl,
      ObjectMapper mapper) {
    return new HttpCatalogueClient(workloadClient(builder, baseUrl, Duration.ofSeconds(30)), mapper);
  }

  @Bean
  RuntimePort runtimePort(RestClient.Builder builder, @Value("${fabric.runtime-url}") String baseUrl) {
    return new HttpRuntimeClient(workloadClient(builder, baseUrl, Duration.ofSeconds(310)));
  }

  @Bean
  FreezeStore freezeStore(NamedParameterJdbcTemplate jdbc) {
    return new JdbcFreezeStore(jdbc);
  }

  @Bean
  JobsService jobsService(
      DecidePort decide,
      CataloguePort catalogue,
      RuntimePort runtime,
      FreezeStore freeze,
      BusinessEvents events,
      AuditPort audit) {
    return new JobsService(decide, catalogue, runtime, freeze, events, audit);
  }

  @Bean
  AssistantService assistantService(
      DecidePort decide,
      CataloguePort catalogue,
      RuntimePort runtime,
      FreezeStore freeze,
      BusinessEvents events,
      AuditPort audit) {
    return new AssistantService(decide, catalogue, runtime, freeze, events, audit);
  }

  @Bean
  AuditPort auditPort(
      RestClient.Builder builder, @Value("${fabric.audit-data-plane-url:}") String baseUrl) {
    if (baseUrl == null || baseUrl.isBlank()) {
      return AuditPort.NOOP;
    }
    return new HttpAuditClient(workloadClient(builder, baseUrl, Duration.ofSeconds(5)), true);
  }

  private static RestClient workloadClient(
      RestClient.Builder builder, String baseUrl, Duration readTimeout) {
    // JDK HttpClient defaults toward HTTP/2 / h2c upgrade. Uvicorn on AR is HTTP/1.1 only.
    // Source: https://docs.spring.io/spring-framework/reference/integration/rest-clients.html
    // Injected RestClient.Builder carries Micrometer observation / W3C propagation.
    HttpClient jdk =
        HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    JdkClientHttpRequestFactory factory = new JdkClientHttpRequestFactory(jdk);
    factory.setReadTimeout(readTimeout);
    return builder
        .requestFactory(factory)
        .requestInterceptor(new RequestIdInterceptor())
        .baseUrl(baseUrl)
        .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer fabric-internal")
        .defaultHeader("X-Workload", "afd")
        .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
        .build();
  }
}
