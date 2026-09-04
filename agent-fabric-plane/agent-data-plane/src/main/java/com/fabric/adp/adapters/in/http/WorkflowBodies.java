package com.fabric.adp.adapters.in.http;

import com.fabric.adp.domain.Workflow;
import com.fabric.adp.domain.WorkflowStage;
import java.util.LinkedHashMap;
import java.util.Map;

final class WorkflowBodies {

  private WorkflowBodies() {}

  static Map<String, Object> toBody(Workflow workflow) {
    if (workflow == null) {
      return null;
    }
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("workflow_id", workflow.workflowId());
    body.put("workflow_version", workflow.workflowVersion());
    body.put("description", workflow.description());
    body.put("status", workflow.status());
    body.put("stages", workflow.stages().stream().map(WorkflowBodies::stageBody).toList());
    return body;
  }

  private static Map<String, Object> stageBody(WorkflowStage stage) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("id", stage.id());
    body.put("tool", stage.tool());
    body.put("type", stage.type());
    body.put("llm_role", stage.llmRole());
    body.put("corpus", stage.corpus());
    body.put("side_effect", stage.sideEffect());
    body.put("requires_approval", stage.requiresApproval());
    body.put("branch", stage.branch());
    body.put("allowlist", stage.allowlist().isEmpty() ? null : stage.allowlist());
    body.put("max_tool_calls", stage.maxToolCalls());
    body.put("waiting_message", stage.waitingMessage());
    return body;
  }
}
