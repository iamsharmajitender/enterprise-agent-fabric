package com.fabric.registry.adapters.in.http;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fabric.registry.application.CapabilityService;
import com.fabric.registry.domain.CapabilityVersion;
import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CapabilityController {

  private final CapabilityService capabilities;
  private final ObjectMapper mapper;

  public CapabilityController(CapabilityService capabilities, ObjectMapper mapper) {
    this.capabilities = capabilities;
    this.mapper = mapper;
  }

  @GetMapping("/v1/capabilities")
  public Map<String, Object> list(
      @RequestParam(name = "q", defaultValue = "") String q,
      @RequestParam(name = "include", required = false) String include) {
    List<Map<String, Object>> items =
        ("all".equals(include) ? capabilities.listAll(q) : capabilities.searchPublished(q))
            .stream()
            .map(this::toBody)
            .toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("capabilities", items);
    return body;
  }

  @GetMapping("/v1/capabilities/{id}")
  public Map<String, Object> latest(@PathVariable String id, HttpServletRequest request) {
    String workload = (String) request.getAttribute(WorkloadAuthFilter.ATTR_WORKLOAD);
    return toBody(capabilities.latest(id, workload));
  }

  @GetMapping("/v1/capabilities/{id}/versions")
  public Map<String, Object> versions(@PathVariable String id, HttpServletRequest request) {
    String workload = (String) request.getAttribute(WorkloadAuthFilter.ATTR_WORKLOAD);
    List<Map<String, Object>> versions =
        capabilities.versions(id, workload).stream().map(this::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("id", id);
    body.put("versions", versions);
    return body;
  }

  @PutMapping("/v1/capabilities/{id}/versions/{version}")
  public ResponseEntity<Map<String, Object>> put(
      @PathVariable String id,
      @PathVariable String version,
      @RequestBody Map<String, Object> body) {
    CapabilityVersion saved = capabilities.put(fromBody(id, version, body));
    return ResponseEntity.ok(toBody(saved));
  }

  @GetMapping("/v1/capabilities/{id}/versions/{version}")
  public Map<String, Object> get(
      @PathVariable String id, @PathVariable String version, HttpServletRequest request) {
    String workload = (String) request.getAttribute(WorkloadAuthFilter.ATTR_WORKLOAD);
    return toBody(capabilities.get(id, version, workload));
  }

  private CapabilityVersion fromBody(String id, String version, Map<String, Object> body) {
    return new CapabilityVersion(
        id,
        version,
        string(body.get("kind")),
        string(body.get("description")),
        json(body.get("input_schema")),
        json(body.get("output_schema")),
        json(body.get("invoke")),
        string(body.get("snippet")),
        string(body.get("owner")),
        string(body.getOrDefault("status", "draft")));
  }

  private Map<String, Object> toBody(CapabilityVersion capability) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("id", capability.id());
    body.put("version", capability.version());
    body.put("kind", capability.kind());
    body.put("description", capability.description());
    body.put("input_schema", tree(capability.inputSchemaJson()));
    if (capability.outputSchemaJson() != null) {
      body.put("output_schema", tree(capability.outputSchemaJson()));
    }
    body.put("invoke", tree(capability.invokeJson()));
    body.put("snippet", capability.snippet());
    body.put("owner", capability.owner());
    body.put("status", capability.status());
    return body;
  }

  private static String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }

  private String json(Object value) {
    if (value == null) {
      return null;
    }
    try {
      return mapper.writeValueAsString(value);
    } catch (JsonProcessingException e) {
      throw new IllegalArgumentException("invalid json field", e);
    }
  }

  private JsonNode tree(String json) {
    try {
      return json == null ? null : mapper.readTree(json);
    } catch (JsonProcessingException e) {
      throw new IllegalStateException(e);
    }
  }
}
