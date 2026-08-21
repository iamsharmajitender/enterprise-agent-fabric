package com.fabric.registry.adapters.in.http;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fabric.registry.application.ManifestService;
import com.fabric.registry.domain.ManifestVersion;
import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ManifestController {

  private final ManifestService manifests;
  private final ObjectMapper mapper;

  public ManifestController(ManifestService manifests, ObjectMapper mapper) {
    this.manifests = manifests;
    this.mapper = mapper;
  }

  @PutMapping("/v1/manifests/{manifestId}/versions/{manifestVersion}")
  public ResponseEntity<Map<String, Object>> put(
      @PathVariable String manifestId,
      @PathVariable String manifestVersion,
      @RequestBody Map<String, Object> body) {
    String status = body.get("status") == null ? "published" : String.valueOf(body.get("status"));
    ManifestVersion saved =
        manifests.put(
            new ManifestVersion(manifestId, manifestVersion, json(body.get("tools")), status));
    return ResponseEntity.ok(toBody(saved));
  }

  @GetMapping("/v1/manifests/{manifestId}/versions/{manifestVersion}")
  public Map<String, Object> get(
      @PathVariable String manifestId,
      @PathVariable String manifestVersion,
      HttpServletRequest request) {
    String workload = (String) request.getAttribute(WorkloadAuthFilter.ATTR_WORKLOAD);
    return toBody(manifests.get(manifestId, manifestVersion, workload));
  }

  private Map<String, Object> toBody(ManifestVersion manifest) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("manifest_id", manifest.manifestId());
    body.put("manifest_version", manifest.manifestVersion());
    body.put("tools", tree(manifest.toolsJson()));
    body.put("status", manifest.status());
    return body;
  }

  private String json(Object value) {
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
