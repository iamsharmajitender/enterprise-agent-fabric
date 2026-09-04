package com.fabric.adp.domain;

import java.util.List;
import java.util.Map;

public record WorkflowStage(
    String id,
    String tool,
    String type,
    String llmRole,
    String corpus,
    Boolean sideEffect,
    Boolean requiresApproval,
    Map<String, String> branch,
    List<String> allowlist,
    Integer maxToolCalls,
    String waitingMessage) {

  public WorkflowStage {
    branch = branch == null ? Map.of() : Map.copyOf(branch);
    allowlist = allowlist == null ? List.of() : List.copyOf(allowlist);
  }
}
