package com.fabric.registry.adapters.in.http;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fabric.registry.application.AuditPort;
import com.fabric.registry.application.InMemoryManifestStore;
import com.fabric.registry.application.ManifestService;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.util.StreamUtils;

@WebMvcTest(controllers = {ManifestController.class, ApiExceptionHandler.class})
@Import({WorkloadAuthFilter.class, ManifestControllerTest.MemConfig.class})
class ManifestControllerTest {

  @Autowired private MockMvc mvc;

  @Test
  void putGetAndConflict() throws Exception {
    String body =
        StreamUtils.copyToString(
            getClass().getResourceAsStream("/contracts/manifest-fee-explain.json"),
            StandardCharsets.UTF_8);
    mvc.perform(
            put("/v1/manifests/fee_explain_v1/versions/2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acr")
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.tools[0].capability_id").value("account_fee_lookup"));

    mvc.perform(
            get("/v1/manifests/fee_explain_v1/versions/latest")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isNotFound());

    mvc.perform(
            put("/v1/manifests/fee_explain_v1/versions/2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acr")
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
        .andExpect(status().isConflict());
  }

  @TestConfiguration
  static class MemConfig {
    @Bean
    ManifestService manifestService() {
      return new ManifestService(new InMemoryManifestStore());
    }

    @Bean
    AuditPort auditPort() {
      return AuditPort.NOOP;
    }
  }
}
