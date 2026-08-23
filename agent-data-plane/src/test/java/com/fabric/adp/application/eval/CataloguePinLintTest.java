package com.fabric.adp.application.eval;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.InMemoryCorpusStore;
import com.fabric.adp.application.InMemoryManifestStore;
import com.fabric.adp.application.InMemoryPromptStore;
import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.application.InMemoryWorkflowStore;
import com.fabric.adp.domain.RouteRow;
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
    RouteRow chat =
        routes.allRoutes().stream()
            .filter(row -> "agent-chat".equals(row.routeId()))
            .findFirst()
            .orElseThrow();
    RouteRow broken =
        new RouteRow(
            chat.routeId(),
            chat.routeVersion(),
            chat.active(),
            chat.intentLabel(),
            chat.description(),
            chat.activationTarget(),
            chat.agentClientId(),
            InMemoryManifestStore.feeExplain(),
            chat.policyProfile(),
            chat.modelProfile(),
            chat.retrieval(),
            chat.memoryProfile(),
            chat.workflowId(),
            chat.promptId(),
            chat.outputSchemaId(),
            chat.evalSuiteId(),
            chat.maxLoopSteps(),
            chat.fallback(),
            chat.requiredClaims(),
            chat.channels(),
            chat.chatVisible(),
            chat.keywords(),
            chat.autonomyMode());
    List<RouteRow> mix = new ArrayList<>(routes.allRoutes());
    mix.replaceAll(row -> "agent-chat".equals(row.routeId()) ? broken : row);
    assertThat(lint(mix)).anyMatch(msg -> msg.contains("Pattern 0 must not have tools"));
  }

  private List<String> lint(List<RouteRow> rows) {
    return CataloguePinLint.lint(rows, prompts, workflows, manifests, corpora);
  }
}
