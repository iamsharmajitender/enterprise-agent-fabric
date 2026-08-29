package com.fabric.adp.adapters.in.http;

import com.fabric.adp.domain.ManifestTool;
import com.fabric.adp.domain.ToolManifest;
import java.util.LinkedHashMap;
import java.util.Map;

final class ManifestBodies {

  private ManifestBodies() {}

  static Map<String, Object> toBody(ToolManifest manifest) {
    if (manifest == null) {
      return null;
    }
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("manifest_id", manifest.manifestId());
    body.put("manifest_version", manifest.manifestVersion());
    body.put("description", manifest.description());
    body.put("tools", manifest.tools().stream().map(ManifestBodies::toolBody).toList());
    body.put("status", manifest.status());
    return body;
  }

  private static Map<String, Object> toolBody(ManifestTool tool) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("name", tool.name());
    body.put("capability_id", tool.capabilityId());
    body.put("capability_version", tool.capabilityVersion());
    body.put("pdp_action", tool.pdpAction());
    body.put("risk_tier", tool.riskTier());
    return body;
  }
}
