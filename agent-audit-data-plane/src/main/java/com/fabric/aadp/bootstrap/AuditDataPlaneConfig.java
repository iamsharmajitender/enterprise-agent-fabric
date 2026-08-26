package com.fabric.aadp.bootstrap;

import com.fabric.aadp.application.AuditEventService;
import com.fabric.aadp.application.AuditEventStore;
import com.fabric.aadp.application.HealthService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AuditDataPlaneConfig {

  @Bean
  HealthService healthService() {
    return new HealthService();
  }

  @Bean
  AuditEventService auditEventService(AuditEventStore store) {
    return new AuditEventService(store);
  }
}
