package com.fabric.registry.adapters.in.http;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fabric.registry.application.CapabilityService;
import com.fabric.registry.application.InMemoryCapabilityStore;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.util.StreamUtils;

import java.nio.charset.StandardCharsets;

@WebMvcTest(controllers = {CapabilityController.class, ApiExceptionHandler.class})
@Import({WorkloadAuthFilter.class, CapabilityControllerTest.MemConfig.class})
class CapabilityControllerTest {

  @Autowired private MockMvc mvc;

  @Test
  void putThenGetPublished() throws Exception {
    String body =
        StreamUtils.copyToString(
            getClass().getResourceAsStream("/contracts/capability-account-fee-lookup.json"),
            StandardCharsets.UTF_8);
    mvc.perform(
            put("/v1/capabilities/account_fee_lookup/versions/1.0.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acr")
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.status").value("published"));

    mvc.perform(
            get("/v1/capabilities/account_fee_lookup/versions/1.0.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.id").value("account_fee_lookup"));

    mvc.perform(
            put("/v1/capabilities/account_fee_lookup/versions/1.0.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acr")
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
        .andExpect(status().isConflict());
  }

  @Test
  void putThenGetOcrExtract() throws Exception {
    String body =
        StreamUtils.copyToString(
            getClass().getResourceAsStream("/contracts/capability-ocr-extract.json"),
            StandardCharsets.UTF_8);
    mvc.perform(
            put("/v1/capabilities/ocr_extract/versions/1.2.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acr")
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.kind").value("domain"))
        .andExpect(jsonPath("$.owner").value("document-intel"))
        .andExpect(jsonPath("$.input_schema.required[0]").value("doc_id"))
        .andExpect(jsonPath("$.invoke.url").value("https://api.internal/ocr/extract"));

    mvc.perform(
            get("/v1/capabilities/ocr_extract/versions/1.2.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.id").value("ocr_extract"))
        .andExpect(jsonPath("$.version").value("1.2.0"))
        .andExpect(jsonPath("$.status").value("published"));
  }

  @Test
  void putThenGetAgentStartWithoutOutputSchema() throws Exception {
    String body =
        StreamUtils.copyToString(
            getClass().getResourceAsStream("/contracts/capability-start-contract-review.json"),
            StandardCharsets.UTF_8);
    mvc.perform(
            put("/v1/capabilities/start_contract_review/versions/1.0.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acr")
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.kind").value("agent_start"))
        .andExpect(jsonPath("$.invoke.body.route_id").value("contract_review"))
        .andExpect(jsonPath("$.output_schema").doesNotExist());

    mvc.perform(
            get("/v1/capabilities/start_contract_review/versions/1.0.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "ar"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.id").value("start_contract_review"))
        .andExpect(jsonPath("$.owner").value("legal-agents"));
  }

  @Test
  void channelBearerIsUnauthorized() throws Exception {
    mvc.perform(get("/v1/capabilities/account_fee_lookup/versions/1.0.0"))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void listAndLatestAndVersions() throws Exception {
    String body =
        StreamUtils.copyToString(
            getClass().getResourceAsStream("/contracts/capability-ocr-extract.json"),
            StandardCharsets.UTF_8);
    String v1 = body.replace("ocr_extract", "list_demo").replace("1.2.0", "1.0.0");
    String v2 = body.replace("ocr_extract", "list_demo");
    mvc.perform(
            put("/v1/capabilities/list_demo/versions/1.0.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acr")
                .contentType(MediaType.APPLICATION_JSON)
                .content(v1))
        .andExpect(status().isOk());
    mvc.perform(
            put("/v1/capabilities/list_demo/versions/1.2.0")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acr")
                .contentType(MediaType.APPLICATION_JSON)
                .content(v2))
        .andExpect(status().isOk());

    mvc.perform(
            get("/v1/capabilities")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.capabilities[?(@.id=='list_demo')]").isNotEmpty());

    mvc.perform(
            get("/v1/capabilities/list_demo")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.version").value("1.2.0"));

    mvc.perform(
            get("/v1/capabilities/list_demo/versions")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.versions.length()").value(2))
        .andExpect(jsonPath("$.versions[0].version").value("1.2.0"));
  }

  @TestConfiguration
  static class MemConfig {
    @Bean
    CapabilityService capabilityService() {
      return new CapabilityService(new InMemoryCapabilityStore());
    }
  }
}
