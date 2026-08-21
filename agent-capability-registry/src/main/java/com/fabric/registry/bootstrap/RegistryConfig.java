package com.fabric.registry.bootstrap;

import com.fabric.registry.adapters.out.jdbc.JdbcCapabilityStore;
import com.fabric.registry.adapters.out.jdbc.JdbcManifestStore;
import com.fabric.registry.application.CapabilityService;
import com.fabric.registry.application.CapabilityStore;
import com.fabric.registry.application.HealthService;
import com.fabric.registry.application.ManifestService;
import com.fabric.registry.application.ManifestStore;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

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
}
