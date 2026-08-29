package com.fabric.adp.adapters.in.http;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fabric.adp.application.CatalogueService;
import com.fabric.adp.application.CorpusService;
import com.fabric.adp.application.DecideService;
import com.fabric.adp.application.InMemoryCorpusStore;
import com.fabric.adp.application.InMemoryIntentRuleStore;
import com.fabric.adp.application.InMemoryManifestStore;
import com.fabric.adp.application.InMemoryPromptStore;
import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.application.InMemoryWorkflowStore;
import com.fabric.adp.application.ManifestService;
import com.fabric.adp.application.PromptService;
import com.fabric.adp.application.WorkflowService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(
    controllers = {
      CatalogController.class,
      ManifestController.class,
      PromptController.class,
      CorpusController.class,
      WorkflowController.class,
      DecideController.class,
      ApiExceptionHandler.class
    })
@Import({WorkloadAuthFilter.class, CatalogAndDecideControllerTest.MemConfig.class})
class CatalogAndDecideControllerTest {

  @Autowired private MockMvc mvc;

  @Test
  void listsRoutesAndGetsShopassistCase() throws Exception {
    mvc.perform(
            get("/v1/catalog/routes")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.routes[?(@.route_id=='shopassist_case')]").exists());

    mvc.perform(
            get("/v1/catalog/routes/shopassist_case")
                .queryParam("route_version", "2026.08.1")
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "acp"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.tool_manifest").value("shopassist_case"))
        .andExpect(jsonPath("$.route_version").value("2026.08.1"))
        .andExpect(jsonPath("$.active").value(true))
        .andExpect(jsonPath("$.model_profile").value("reasoning-standard"))
        .andExpect(jsonPath("$.manifest.manifest_id").value("shopassist_case"))
        .andExpect(jsonPath("$.manifest.tools[0].name").value("lookup_order"))
        .andExpect(jsonPath("$.prompt_id").value("shopassist_case"))
        .andExpect(jsonPath("$.autonomy_mode").value(1));
  }

  @Test
  void decideRoutesShopassistUtterance() throws Exception {
    mvc.perform(
            post("/v1/decide")
                .contentType(MediaType.APPLICATION_JSON)
                .header("Authorization", "Bearer fabric-internal")
                .header("X-Workload", "afd")
                .content(
                    """
                    {
                      "ingress": "chat",
                      "channel": "web",
                      "session_id": "sess-88",
                      "message": "My blue jacket arrived damaged and I want a refund",
                      "claims": {"sub":"jane","emts":{"support:case":true}}
                    }
                    """))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.outcome").value("route"))
        .andExpect(jsonPath("$.route_id").value("shopassist_case"));
  }

  @TestConfiguration
  static class MemConfig {
    @Bean
    CatalogueService catalogueService() {
      return new CatalogueService(new InMemoryRouteStore().seedDemo());
    }

    @Bean
    ManifestService manifestService() {
      return new ManifestService(new InMemoryManifestStore().seedDemo());
    }

    @Bean
    PromptService promptService() {
      return new PromptService(new InMemoryPromptStore().seedDemo());
    }

    @Bean
    CorpusService corpusService() {
      return new CorpusService(new InMemoryCorpusStore().seedDemo());
    }

    @Bean
    WorkflowService workflowService() {
      return new WorkflowService(new InMemoryWorkflowStore().seedDemo());
    }

    @Bean
    DecideService decideService(CatalogueService catalogue) {
      return new DecideService(
          catalogue,
          new com.fabric.adp.application.BusinessEvents(
              new io.micrometer.core.instrument.simple.SimpleMeterRegistry()),
          new InMemoryIntentRuleStore().seedDemo());
    }
  }
}
