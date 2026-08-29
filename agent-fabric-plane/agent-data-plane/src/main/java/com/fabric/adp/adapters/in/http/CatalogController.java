package com.fabric.adp.adapters.in.http;

import com.fabric.adp.application.CatalogueService;
import com.fabric.adp.domain.MemoryProfile;
import com.fabric.adp.domain.Retrieval;
import com.fabric.adp.domain.RouteRow;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CatalogController {

  private final CatalogueService catalogue;
  private final ObjectMapper mapper;

  public CatalogController(CatalogueService catalogue, ObjectMapper mapper) {
    this.catalogue = catalogue;
    this.mapper = mapper;
  }

  @GetMapping("/v1/catalog/routes")
  public Map<String, Object> list(
      @RequestParam(name = "include", required = false) String include) {
    List<RouteRow> rows = "all".equals(include) ? catalogue.listAll() : catalogue.list();
    List<Map<String, Object>> routes = rows.stream().map(this::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("routes", routes);
    return body;
  }

  @GetMapping("/v1/catalog/routes/{routeId}")
  public Map<String, Object> get(
      @PathVariable String routeId,
      @RequestParam(name = "route_version", required = false) String version) {
    return toBody(catalogue.get(routeId, version));
  }

  @GetMapping("/v1/catalog/routes/{routeId}/versions")
  public Map<String, Object> versions(@PathVariable String routeId) {
    List<Map<String, Object>> versions =
        catalogue.versions(routeId).stream().map(this::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("route_id", routeId);
    body.put("versions", versions);
    return body;
  }

  @GetMapping("/v1/intent/eligible")
  public Map<String, Object> eligible(
      @RequestParam(defaultValue = "web") String channel,
      HttpServletRequest request) {
    Set<String> claims = StubClaims.entitled(request.getHeader("X-Stub-Claims"), mapper);
    List<RouteRow> rows = catalogue.eligible(channel, claims);
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("channel", channel);
    body.put("routes", rows.stream().map(this::toBody).toList());
    return body;
  }

  private Map<String, Object> toBody(RouteRow row) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("route_id", row.routeId());
    body.put("route_version", row.routeVersion());
    body.put("active", row.active());
    body.put("status", row.status());
    body.put("intent_label", row.intentLabel());
    body.put("autonomy_mode", row.autonomyMode().code());
    body.put("description", row.description());
    body.put("activation_target", row.activationTarget());
    body.put("agent_client_id", row.agentClientId());
    body.put("tool_manifest", row.manifest() == null ? null : row.manifest().manifestId());
    body.put(
        "tool_manifest_version",
        row.manifest() == null ? null : row.manifest().manifestVersion());
    body.put("manifest", ManifestBodies.toBody(row.manifest()));
    body.put("policy_profile", row.policyProfile());
    body.put("model_profile", row.modelProfile().id());
    body.put("retrieval", retrievalBody(row.retrieval()));
    body.put("memory_profile", memoryBody(row.memoryProfile()));
    body.put("workflow_id", row.workflowId());
    body.put("prompt_id", row.promptId());
    body.put("output_schema_id", row.outputSchemaId());
    body.put("eval_suite_id", row.evalSuiteId());
    body.put("max_loop_steps", row.maxLoopSteps());
    body.put("fallback", row.fallback());
    body.put("required_claims", row.requiredClaims());
    body.put("channels", row.channels());
    body.put("chat_visible", row.chatVisible());
    return body;
  }

  private static Map<String, Object> retrievalBody(Retrieval retrieval) {
    if (retrieval == null || !Retrieval.hasMode(retrieval.mode())) {
      return null;
    }
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("mode", retrieval.mode());
    body.put("scope", retrieval.scope());
    return body;
  }

  private static Map<String, Object> memoryBody(MemoryProfile memory) {
    if (memory == null) {
      return null;
    }
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("conversation", memory.conversation());
    body.put("working", memory.working());
    body.put("loop", memory.loop());
    body.put("long_term", memory.longTerm());
    body.put("ttl_hours", memory.ttlHours());
    body.put("isolation", memory.isolation());
    return body;
  }
}
