package com.fabric.adp.bootstrap;

import com.fabric.adp.adapters.out.http.HttpAuditClient;
import com.fabric.adp.adapters.out.jdbc.JdbcCorpusStore;
import com.fabric.adp.adapters.out.jdbc.JdbcIntentRuleStore;
import com.fabric.adp.adapters.out.jdbc.JdbcManifestStore;
import com.fabric.adp.adapters.out.jdbc.JdbcPromptStore;
import com.fabric.adp.adapters.out.jdbc.JdbcRouteStore;
import com.fabric.adp.adapters.out.jdbc.JdbcWorkflowStore;
import com.fabric.adp.application.AuditPort;
import com.fabric.adp.application.BusinessEvents;
import com.fabric.adp.application.CatalogueService;
import com.fabric.adp.application.CorpusService;
import com.fabric.adp.application.CorpusStore;
import com.fabric.adp.application.DecideService;
import com.fabric.adp.application.HealthService;
import com.fabric.adp.application.IntentRuleStore;
import com.fabric.adp.application.ManifestService;
import com.fabric.adp.application.ManifestStore;
import com.fabric.adp.application.PromptService;
import com.fabric.adp.application.PromptStore;
import com.fabric.adp.application.RouteStore;
import com.fabric.adp.application.WorkflowService;
import com.fabric.adp.application.WorkflowStore;
import com.fabric.adp.application.layers.LlmFallbackPool;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.web.client.RestClient;

import java.util.concurrent.ExecutorService;

@Configuration
public class DataPlaneConfig {

  @Bean
  HealthService healthService() {
    return new HealthService();
  }

  @Bean
  RouteStore routeStore(NamedParameterJdbcTemplate jdbc, ObjectMapper mapper) {
    return new JdbcRouteStore(jdbc, mapper);
  }

  @Bean
  ManifestStore manifestStore(NamedParameterJdbcTemplate jdbc, ObjectMapper mapper) {
    return new JdbcManifestStore(jdbc, mapper);
  }

  @Bean
  CatalogueService catalogueService(RouteStore store) {
    return new CatalogueService(store);
  }

  @Bean
  ManifestService manifestService(ManifestStore store) {
    return new ManifestService(store);
  }

  @Bean
  PromptStore promptStore(NamedParameterJdbcTemplate jdbc) {
    return new JdbcPromptStore(jdbc);
  }

  @Bean
  PromptService promptService(PromptStore store) {
    return new PromptService(store);
  }

  @Bean
  CorpusStore corpusStore(NamedParameterJdbcTemplate jdbc) {
    return new JdbcCorpusStore(jdbc);
  }

  @Bean
  CorpusService corpusService(CorpusStore store) {
    return new CorpusService(store);
  }

  @Bean
  WorkflowStore workflowStore(NamedParameterJdbcTemplate jdbc, ObjectMapper mapper) {
    return new JdbcWorkflowStore(jdbc, mapper);
  }

  @Bean
  WorkflowService workflowService(WorkflowStore store) {
    return new WorkflowService(store);
  }

  @Bean
  BusinessEvents businessEvents(MeterRegistry meters) {
    return new BusinessEvents(meters);
  }

  @Bean
  IntentRuleStore intentRuleStore(NamedParameterJdbcTemplate jdbc) {
    return new JdbcIntentRuleStore(jdbc);
  }

  @Bean(destroyMethod = "shutdownNow")
  ExecutorService llmFallbackPool() {
    return LlmFallbackPool.create();
  }

  @Bean
  DecideService decideService(
      CatalogueService catalogue,
      BusinessEvents events,
      IntentRuleStore rules,
      ExecutorService llmFallbackPool,
      AuditPort audit,
      @Value("${fabric.decide.llm.enabled:false}") boolean llmEnabled,
      @Value("${fabric.decide.llm.timeout-ms:500}") long llmTimeoutMs) {
    return new DecideService(
        catalogue, events, rules, llmEnabled, llmFallbackPool, llmTimeoutMs, audit);
  }

  @Bean
  AuditPort auditPort(
      RestClient.Builder builder,
      @Value("${fabric.audit-data-plane-url:}") String baseUrl) {
    if (baseUrl == null || baseUrl.isBlank()) {
      return AuditPort.NOOP;
    }
    RestClient client =
        builder
            .baseUrl(baseUrl)
            .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer fabric-internal")
            .defaultHeader("X-Workload", "adp")
            .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
            .build();
    return new HttpAuditClient(client, true);
  }
}