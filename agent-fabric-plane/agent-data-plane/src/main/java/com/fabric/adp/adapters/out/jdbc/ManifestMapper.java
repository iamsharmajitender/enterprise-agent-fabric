package com.fabric.adp.adapters.out.jdbc;

import com.fabric.adp.domain.ManifestTool;
import com.fabric.adp.domain.ToolManifest;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.List;

public final class ManifestMapper {

  private final ObjectMapper mapper;

  public ManifestMapper(ObjectMapper mapper) {
    this.mapper = mapper;
  }

  public ToolManifest parse(String id, String version, String description, String toolsJson) {
    return parse(id, version, description, toolsJson, "published");
  }

  public ToolManifest parse(
      String id, String version, String description, String toolsJson, String status) {
    if (id == null || version == null) {
      return null;
    }
    String resolved = status == null || status.isBlank() ? "published" : status;
    return new ToolManifest(id, version, description, tools(toolsJson), resolved);
  }

  private List<ManifestTool> tools(String toolsJson) {
    if (toolsJson == null || toolsJson.isBlank()) {
      return List.of();
    }
    try {
      JsonNode array = mapper.readTree(toolsJson);
      List<ManifestTool> tools = new ArrayList<>();
      for (JsonNode node : array) {
        tools.add(
            new ManifestTool(
                text(node, "name"),
                text(node, "capability_id"),
                text(node, "capability_version"),
                text(node, "pdp_action"),
                text(node, "risk_tier")));
      }
      return List.copyOf(tools);
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  private static String text(JsonNode node, String field) {
    JsonNode value = node.get(field);
    return value == null || value.isNull() ? null : value.asText();
  }
}
