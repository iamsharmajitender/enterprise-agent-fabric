package com.fabric.adp.application.eval;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.InMemoryCorpusStore;
import com.fabric.adp.application.InMemoryManifestStore;
import com.fabric.adp.application.InMemoryPromptStore;
import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.application.InMemoryWorkflowStore;
import com.fabric.adp.domain.RouteRow;
import com.fabric.adp.domain.ToolManifest;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class CataloguePinLintTest {

  private final InMemoryRouteStore routes = new InMemoryRouteStore().seedDemo();
  private final InMemoryPromptStore prompts = new InMemoryPromptStore().seedDemo();
  private final InMemoryWorkflowStore workflows = new InMemoryWorkflowStore().seedDemo();
  private final InMemoryManifestStore manifests = new InMemoryManifestStore().seedDemo();
  private final InMemoryCorpusStore corpora = new InMemoryCorpusStore().seedDemo();

  @Test
  void catalogueSeedIsPinClean() {
    assertThat(lint(routes.allRoutes())).isEmpty();
  }

  @Test
  void patternZeroWithToolsFails() {
    List<RouteRow> mix = replaceChat(withManifest(chatRoute(), InMemoryManifestStore.feeExplain()));
    assertThat(lint(mix)).anyMatch(msg -> msg.contains("Pattern 0 must not have tools"));
  }

  @Test
  void activeRouteWithoutPromptIdFails() {
    List<RouteRow> mix = replaceChat(withPromptId(chatRoute(), null));
    assertThat(lint(mix)).anyMatch(msg -> msg.contains("every route must have a prompt_id"));
  }

  private RouteRow chatRoute() {
    return routes.allRoutes().stream()
        .filter(row -> "agent-chat".equals(row.routeId()))
        .findFirst()
        .orElseThrow();
  }

  private List<RouteRow> replaceChat(RouteRow broken) {
    List<RouteRow> mix = new ArrayList<>(routes.allRoutes());
    mix.replaceAll(row -> "agent-chat".equals(row.routeId()) ? broken : row);
    return mix;
  }

  private List<String> lint(List<RouteRow> rows) {
    return CataloguePinLint.lint(rows, prompts, workflows, manifests, corpora);
  }

  private static RouteRow withManifest(RouteRow row, ToolManifest manifest) {
    return copy(row, manifest, row.promptId());
  }

  private static RouteRow withPromptId(RouteRow row, String promptId) {
    return copy(row, row.manifest(), promptId);
  }

  private static RouteRow copy(RouteRow row, ToolManifest manifest, String promptId) {
    return new RouteRow(
        row.routeId(),
        row.routeVersion(),
        row.active(),
        row.intentLabel(),
        row.description(),
        row.activationTarget(),
        row.agentClientId(),
        manifest,
        row.policyProfile(),
        row.modelProfile(),
        row.retrieval(),
        row.memoryProfile(),
        row.workflowId(),
        promptId,
        row.outputSchemaId(),
        row.evalSuiteId(),
        row.maxLoopSteps(),
        row.fallback(),
        row.requiredClaims(),
        row.channels(),
        row.chatVisible(),
        row.keywords(),
        row.autonomyMode());
  }
}
