package com.fabric.adp.application;

import com.fabric.adp.domain.NotFoundException;
import com.fabric.adp.domain.Workflow;
import java.util.List;

public class WorkflowService {

  private final WorkflowStore store;

  public WorkflowService(WorkflowStore store) {
    this.store = store;
  }

  public Workflow get(String workflowId, String workflowVersion) {
    return store
        .find(workflowId, workflowVersion)
        .orElseThrow(() -> new NotFoundException(workflowId + "@" + workflowVersion));
  }

  public Workflow latest(String workflowId) {
    List<Workflow> found = store.listVersions(workflowId);
    if (found.isEmpty()) {
      throw new NotFoundException(workflowId);
    }
    return found.getFirst();
  }

  public List<Workflow> listLatest() {
    return store.listLatest();
  }

  public List<Workflow> listAll() {
    return store.listAll();
  }

  public List<Workflow> versions(String workflowId) {
    List<Workflow> found = store.listVersions(workflowId);
    if (found.isEmpty()) {
      throw new NotFoundException(workflowId);
    }
    return found;
  }
}
