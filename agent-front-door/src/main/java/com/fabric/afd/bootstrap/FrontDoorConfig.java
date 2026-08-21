package com.fabric.afd.bootstrap;

import com.fabric.afd.adapters.out.http.HttpCatalogueClient;
import com.fabric.afd.adapters.out.http.HttpDecideClient;
import com.fabric.afd.adapters.out.http.HttpRuntimeClient;
import com.fabric.afd.adapters.out.jdbc.JdbcFreezeStore;
import com.fabric.afd.application.AssistantService;
import com.fabric.afd.application.CataloguePort;
import com.fabric.afd.application.DecidePort;
import com.fabric.afd.application.FreezeStore;
import com.fabric.afd.application.HealthService;
import com.fabric.afd.application.JobsService;
import com.fabric.afd.application.RuntimePort;
import com.fasterxml.jackson.databind.ObjectMapper;
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
  DecidePort decidePort(@Value("${fabric.data-plane-url}") String baseUrl) {
    return new HttpDecideClient(workloadClient(baseUrl));
  }

  @Bean
  CataloguePort cataloguePort(
      @Value("${fabric.data-plane-url}") String baseUrl, ObjectMapper mapper) {
    return new HttpCatalogueClient(workloadClient(baseUrl), mapper);
  }

  @Bean
  RuntimePort runtimePort(@Value("${fabric.runtime-url}") String baseUrl) {
    return new HttpRuntimeClient(workloadClient(baseUrl));
  }

  @Bean
  FreezeStore freezeStore(NamedParameterJdbcTemplate jdbc) {
    return new JdbcFreezeStore(jdbc);
  }

  @Bean
  JobsService jobsService(
      DecidePort decide, CataloguePort catalogue, RuntimePort runtime, FreezeStore freeze) {
    return new JobsService(decide, catalogue, runtime, freeze);
  }

  @Bean
  AssistantService assistantService(
      DecidePort decide, CataloguePort catalogue, RuntimePort runtime, FreezeStore freeze) {
    return new AssistantService(decide, catalogue, runtime, freeze);
  }

  private static RestClient workloadClient(String baseUrl) {
    // JDK HttpClient defaults toward HTTP/2 / h2c upgrade. Uvicorn on AR is HTTP/1.1 only.
    // Source: https://docs.spring.io/spring-framework/reference/integration/rest-clients.html
    HttpClient jdk =
        HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    JdkClientHttpRequestFactory factory = new JdkClientHttpRequestFactory(jdk);
    factory.setReadTimeout(Duration.ofSeconds(30));
    return RestClient.builder()
        .requestFactory(factory)
        .baseUrl(baseUrl)
        .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer fabric-internal")
        .defaultHeader("X-Workload", "afd")
        .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
        .build();
  }
}

