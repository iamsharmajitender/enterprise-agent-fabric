package com.fabric.adp.adapters.in.http;

import com.fabric.adp.application.ManifestService;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ManifestController {

  private final ManifestService manifests;

  public ManifestController(ManifestService manifests) {
    this.manifests = manifests;
  }

  @GetMapping("/v1/catalog/manifests")
  public Map<String, Object> list(
      @RequestParam(name = "include", required = false) String include) {
    List<Map<String, Object>> items =
        ("all".equals(include) ? manifests.listAll() : manifests.listLatest())
            .stream().map(ManifestBodies::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("manifests", items);
    return body;
  }

  @GetMapping("/v1/catalog/manifests/{manifestId}")
  public Map<String, Object> latest(@PathVariable String manifestId) {
    return ManifestBodies.toBody(manifests.latest(manifestId));
  }

  @GetMapping("/v1/catalog/manifests/{manifestId}/versions")
  public Map<String, Object> versions(@PathVariable String manifestId) {
    List<Map<String, Object>> versions =
        manifests.versions(manifestId).stream().map(ManifestBodies::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("manifest_id", manifestId);
    body.put("versions", versions);
    return body;
  }

  @GetMapping("/v1/catalog/manifests/{manifestId}/versions/{manifestVersion}")
  public Map<String, Object> get(
      @PathVariable String manifestId, @PathVariable String manifestVersion) {
    return ManifestBodies.toBody(manifests.get(manifestId, manifestVersion));
  }
}
