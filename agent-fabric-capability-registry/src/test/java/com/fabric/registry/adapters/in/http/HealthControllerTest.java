package com.fabric.registry.adapters.in.http;

import com.fabric.registry.application.HealthService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(HealthController.class)
@Import(HealthControllerTest.HealthOnlyConfig.class)
class HealthControllerTest {

  @Autowired
  private MockMvc mvc;

  @Test
  void healthReturnsUp() throws Exception {
    mvc.perform(get("/health"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.status").value("UP"));
  }

  @TestConfiguration
  static class HealthOnlyConfig {
    @Bean
    HealthService healthService() {
      return new HealthService();
    }
  }
}
