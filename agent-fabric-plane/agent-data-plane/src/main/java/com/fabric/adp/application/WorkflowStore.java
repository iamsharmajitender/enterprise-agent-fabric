package com.fabric.adp.application;

import com.fabric.adp.domain.Workflow;
import java.util.List;
import java.util.Optional;

public interface WorkflowStore {

  Optional<Workflow> find(String workflowId, String workflowVersion);

  List<Workflow> listLatest();

  List<Workflow> listAll();

  List<Workflow> listVersions(String workflowId);
}
