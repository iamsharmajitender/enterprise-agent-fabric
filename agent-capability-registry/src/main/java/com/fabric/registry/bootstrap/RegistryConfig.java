package com.fabric.registry.bootstrap;

import com.fabric.registry.adapters.out.http.HttpAuditClient;
import com.fabric.registry.adapters.out.jdbc.JdbcCapabilityStore;
import com.fabric.registry.adapters.out.jdbc.JdbcManifestStore;
import com.fabric.registry.application.AuditPort;
import com.fabric.registry.application.CapabilityService;
import com.fabric.registry.application.CapabilityStore;
import com.fabric.registry.application.HealthService;
import com.fabric.registry.application.ManifestService;
import com.fabric.registry.application.ManifestStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.web.client.RestClient;

@Configuration
public class RegistryConfig {

  @Bean
  HealthService healthService() {
    return new HealthService();
  }

  @Bean
  CapabilityStore capabilityStore(NamedParameterJdbcTemplate jdbc) {
    return new JdbcCapabilityStore(jdbc);
  }

  @Bean
  ManifestStore manifestStore(NamedParameterJdbcTemplate jdbc) {
    return new JdbcManifestStore(jdbc);
  }

  @Bean
  CapabilityService capabilityService(CapabilityStore store) {
    return new CapabilityService(store);
  }

  @Bean
  ManifestService manifestService(ManifestStore store) {
    return new ManifestService(store);
  }

  @Bean
  AuditPort auditPort(
      RestClient.Builder builder, @Value("${fabric.audit-data-plane-url:}") String baseUrl) {
    if (baseUrl == null || baseUrl.isBlank()) {
      return AuditPort.NOOP;
    }
    RestClient client =
        builder
            .baseUrl(baseUrl)
            .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer fabric-internal")
            .defaultHeader("X-Workload", "acr")
            .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
            .build();
    return new HttpAuditClient(client, true);
  }
}
