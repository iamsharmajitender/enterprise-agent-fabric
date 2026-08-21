package com.fabric.adp.bootstrap;

import com.fabric.adp.adapters.out.jdbc.JdbcCorpusStore;
import com.fabric.adp.adapters.out.jdbc.JdbcManifestStore;
import com.fabric.adp.adapters.out.jdbc.JdbcPromptStore;
import com.fabric.adp.adapters.out.jdbc.JdbcRouteStore;
import com.fabric.adp.adapters.out.jdbc.JdbcWorkflowStore;
import com.fabric.adp.application.CatalogueService;
import com.fabric.adp.application.CorpusService;
import com.fabric.adp.application.CorpusStore;
import com.fabric.adp.application.DecideService;
import com.fabric.adp.application.HealthService;
import com.fabric.adp.application.ManifestService;
import com.fabric.adp.application.ManifestStore;
import com.fabric.adp.application.PromptService;
import com.fabric.adp.application.PromptStore;
import com.fabric.adp.application.RouteStore;
import com.fabric.adp.application.WorkflowService;
import com.fabric.adp.application.WorkflowStore;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

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
  DecideService decideService(CatalogueService catalogue) {
    return new DecideService(catalogue);
  }
}
