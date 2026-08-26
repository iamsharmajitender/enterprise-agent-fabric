package com.fabric.adp.application.eval;

import com.fabric.adp.application.CorpusStore;
import com.fabric.adp.application.ManifestStore;
import com.fabric.adp.application.PromptStore;
import com.fabric.adp.application.WorkflowStore;
import com.fabric.adp.domain.AutonomyPattern;
import com.fabric.adp.domain.ManifestTool;
import com.fabric.adp.domain.Retrieval;
import com.fabric.adp.domain.RouteRow;
import com.fabric.adp.domain.ToolManifest;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

final class CataloguePinLint {

  static final Set<String> HIGH_RISK_WRITES =
      Set.of("card_freeze", "account_notify", "kyc_onboarding", "purchase_refund");
  private static final String VERSION = "2026.08.1";

  private CataloguePinLint() {}

  static List<String> lint(
      List<RouteRow> routes,
      PromptStore prompts,
      WorkflowStore workflows,
      ManifestStore manifests,
      CorpusStore corpora) {
    List<String> errors = new ArrayList<>();
    Set<String> knownCapabilities = new LinkedHashSet<>();
    for (ToolManifest published : manifests.listAll()) {
      if (!"published".equals(published.status()) || published.tools() == null) {
        continue;
      }
      for (ManifestTool tool : published.tools()) {
        if (tool.capabilityId() != null && !tool.capabilityId().isBlank()) {
          knownCapabilities.add(tool.capabilityId());
        }
      }
    }
    for (RouteRow row : routes) {
      if (!row.active()) {
        continue;
      }
      String id = row.routeId();
      if (!notBlank(row.promptId())) {
        errors.add(id + ": every route must have a prompt_id");
      }
      if (notBlank(row.promptId())
          && prompts.findPublished(row.promptId()).isEmpty()
          && prompts.find(row.promptId(), VERSION).isEmpty()) {
        errors.add(id + ": prompt_id not in seed: " + row.promptId());
      }
      if (notBlank(row.workflowId())
          && workflows.find(row.workflowId(), VERSION).isEmpty()
          && workflows.listVersions(row.workflowId()).isEmpty()) {
        errors.add(id + ": workflow_id not in seed: " + row.workflowId());
      }
      if (row.manifest() != null) {
        ToolManifest manifest = row.manifest();
        if (manifests.find(manifest.manifestId(), manifest.manifestVersion()).isEmpty()) {
          errors.add(id + ": tool_manifest not in seed: " + manifest.manifestId());
        }
        if (!"published".equals(manifest.status())) {
          errors.add(id + ": tool_manifest is not published");
        }
        if (manifest.tools() != null) {
          for (ManifestTool tool : manifest.tools()) {
            if (tool.capabilityId() == null || tool.capabilityId().isBlank()) {
              errors.add(id + ": blank capability_id on " + tool.name());
            } else if (!knownCapabilities.contains(tool.capabilityId())) {
              errors.add(id + ": unknown capability_id " + tool.capabilityId());
            }
          }
        }
      }
      Retrieval retrieval = row.retrieval();
      if (retrieval != null && retrieval.scope() != null) {
        for (String corpusId : retrieval.scope()) {
          var found = corpora.find(corpusId);
          if (found.isEmpty()) {
            errors.add(id + ": unknown corpus " + corpusId);
          } else if (!"published".equals(found.get().status())) {
            errors.add(id + ": corpus not published " + corpusId);
          }
        }
      }
      if (row.autonomyMode() == AutonomyPattern.SINGLE_INFERENCE) {
        boolean hasTools =
            row.manifest() != null
                && row.manifest().tools() != null
                && !row.manifest().tools().isEmpty();
        if (hasTools) {
          errors.add(id + ": Pattern 0 must not have tools");
        }
        if (notBlank(row.workflowId())) {
          errors.add(id + ": Pattern 0 must not have a workflow");
        }
        if (retrieval != null && "tool".equals(retrieval.mode())) {
          errors.add(id + ": Pattern 0 must not use retrieval.mode=tool");
        }
      }
      if (row.autonomyMode() == AutonomyPattern.DETERMINISTIC && !notBlank(row.workflowId())) {
        errors.add(id + ": Pattern 2 must have a workflow");
      }
      if (HIGH_RISK_WRITES.contains(id) && !notBlank(row.workflowId())) {
        errors.add(id + ": high-risk write must have a workflow");
      }
    }
    return errors;
  }

  private static boolean notBlank(String value) {
    return value != null && !value.isBlank();
  }
}
