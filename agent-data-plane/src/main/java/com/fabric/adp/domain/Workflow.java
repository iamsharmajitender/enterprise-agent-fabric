package com.fabric.adp.domain;

import java.util.List;

public record Workflow(
    String workflowId,
    String workflowVersion,
    String description,
    String status,
    List<WorkflowStage> stages) {

  public Workflow {
    stages = stages == null ? List.of() : List.copyOf(stages);
  }

  public Workflow(
      String workflowId, String workflowVersion, String description, List<WorkflowStage> stages) {
    this(workflowId, workflowVersion, description, "published", stages);
  }
}
