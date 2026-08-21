package com.fabric.adp.adapters.in.http;

import com.fabric.adp.application.WorkflowService;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class WorkflowController {

  private final WorkflowService workflows;

  public WorkflowController(WorkflowService workflows) {
    this.workflows = workflows;
  }

  @GetMapping("/v1/catalog/workflows")
  public Map<String, Object> list(
      @RequestParam(name = "include", required = false) String include) {
    List<Map<String, Object>> items =
        ("all".equals(include) ? workflows.listAll() : workflows.listLatest())
            .stream().map(WorkflowBodies::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("workflows", items);
    return body;
  }

  @GetMapping("/v1/catalog/workflows/{workflowId}")
  public Map<String, Object> latest(@PathVariable String workflowId) {
    return WorkflowBodies.toBody(workflows.latest(workflowId));
  }

  @GetMapping("/v1/catalog/workflows/{workflowId}/versions")
  public Map<String, Object> versions(@PathVariable String workflowId) {
    List<Map<String, Object>> versions =
        workflows.versions(workflowId).stream().map(WorkflowBodies::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("workflow_id", workflowId);
    body.put("versions", versions);
    return body;
  }

  @GetMapping("/v1/catalog/workflows/{workflowId}/versions/{workflowVersion}")
  public Map<String, Object> get(
      @PathVariable String workflowId, @PathVariable String workflowVersion) {
    return WorkflowBodies.toBody(workflows.get(workflowId, workflowVersion));
  }
}
