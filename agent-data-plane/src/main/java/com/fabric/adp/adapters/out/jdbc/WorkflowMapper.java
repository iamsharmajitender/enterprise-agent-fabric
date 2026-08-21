package com.fabric.adp.adapters.out.jdbc;

import com.fabric.adp.domain.Workflow;
import com.fabric.adp.domain.WorkflowStage;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class WorkflowMapper {

  private final ObjectMapper mapper;

  public WorkflowMapper(ObjectMapper mapper) {
    this.mapper = mapper;
  }

  public Workflow parse(
      String id, String version, String description, String stagesJson, String status) {
    if (id == null || version == null) {
      return null;
    }
    String resolved = status == null || status.isBlank() ? "published" : status;
    return new Workflow(id, version, description, resolved, stages(stagesJson));
  }

  private List<WorkflowStage> stages(String stagesJson) {
    if (stagesJson == null || stagesJson.isBlank()) {
      return List.of();
    }
    try {
      JsonNode array = mapper.readTree(stagesJson);
      List<WorkflowStage> stages = new ArrayList<>();
      for (JsonNode node : array) {
        stages.add(
            new WorkflowStage(
                text(node, "id"),
                text(node, "tool"),
                text(node, "type"),
                text(node, "llm_role"),
                text(node, "corpus"),
                bool(node, "side_effect"),
                bool(node, "requires_approval"),
                objectStrings(node.get("branch")),
                stringList(node.get("allowlist")),
                integer(node, "max_tool_calls")));
      }
      return List.copyOf(stages);
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  private static String text(JsonNode node, String field) {
    JsonNode value = node.get(field);
    return value == null || value.isNull() ? null : value.asText();
  }

  private static Boolean bool(JsonNode node, String field) {
    JsonNode value = node.get(field);
    return value == null || value.isNull() || !value.isBoolean() ? null : value.booleanValue();
  }

  private static Integer integer(JsonNode node, String field) {
    JsonNode value = node.get(field);
    return value == null || value.isNull() || !value.isNumber() ? null : value.intValue();
  }

  private static List<String> stringList(JsonNode node) {
    if (node == null || node.isNull() || !node.isArray()) {
      return List.of();
    }
    List<String> out = new ArrayList<>();
    for (JsonNode item : node) {
      if (item != null && !item.isNull()) {
        out.add(item.asText());
      }
    }
    return List.copyOf(out);
  }

  private static Map<String, String> objectStrings(JsonNode node) {
    if (node == null || node.isNull() || !node.isObject()) {
      return Map.of();
    }
    Map<String, String> out = new LinkedHashMap<>();
    node.fields().forEachRemaining(entry -> out.put(entry.getKey(), entry.getValue().asText()));
    return out;
  }
}
