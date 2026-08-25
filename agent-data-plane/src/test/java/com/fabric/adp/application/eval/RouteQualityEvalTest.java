package com.fabric.adp.application.eval;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.application.InMemoryRouteStore;
import com.fabric.adp.application.InMemoryWorkflowStore;
import com.fabric.adp.domain.RouteRow;
import com.fabric.adp.domain.Workflow;
import com.fabric.adp.domain.WorkflowStage;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

/**
 * E14: route-quality tool-sequence gate. Compares fixture {@code expected.stages} to the seeded
 * workflow — no live model.
 */
class RouteQualityEvalTest {

  private final InMemoryRouteStore routes = new InMemoryRouteStore().seedDemo();
  private final InMemoryWorkflowStore workflows = new InMemoryWorkflowStore().seedDemo();

  @ParameterizedTest(name = "{0}/{1}")
  @MethodSource("cases")
  void toolSequenceMatchesSeededWorkflow(String suiteId, String caseId, RouteQualityCase evalCase) {
    assertThat(evalCase.routeId()).isNotBlank();
    assertThat(evalCase.expected()).isNotNull();
    assertThat(evalCase.goal()).isNotEmpty();

    RouteRow route =
        routes
            .activeRoute(evalCase.routeId())
            .orElseThrow(() -> new AssertionError("missing route " + evalCase.routeId()));
    assertThat(route.evalSuiteId())
        .as("%s catalogue eval_suite_id", evalCase.routeId())
        .isEqualTo(suiteId);
    assertThat(route.workflowId())
        .as("%s must have a workflow for tool-sequence", evalCase.routeId())
        .isNotBlank();

    Workflow workflow =
        workflows
            .find(route.workflowId(), route.routeVersion())
            .or(() -> workflows.find(route.workflowId(), "2026.08.1"))
            .orElseThrow(
                () ->
                    new AssertionError(
                        "missing workflow " + route.workflowId() + "@" + route.routeVersion()));

    RouteQualityAssert.assertStageOrder(
        caseId, evalCase.expected().stages(), workflow.stages());
  }

  static Stream<Arguments> cases() {
    return RouteQualityJson.loadAllActiveCases().stream()
        .map(
            loaded ->
                Arguments.of(
                    loaded.suiteId(), loaded.evalCase().id(), loaded.evalCase()));
  }

  @Test
  void agentChatHasNoEvalSuite() {
    RouteRow chat = routes.activeRoute("agent-chat").orElseThrow();
    assertThat(chat.evalSuiteId()).isNullOrEmpty();
    assertThat(chat.workflowId()).isNullOrEmpty();
  }

  @Test
  void everyActiveSuiteIdResolves() {
    Map<String, String> active = RouteQualityJson.activeVersions();
    assertThat(active).isNotEmpty();
    for (String suiteId : active.keySet()) {
      RouteQualityFile file = RouteQualityJson.loadActive(suiteId);
      assertThat(file.cases()).isNotEmpty();
    }
  }

  @Test
  void reorderedWorkflowFailsMatch() {
    RouteQualityCase evalCase =
        RouteQualityJson.loadActive("card_freeze_tools").cases().getFirst();
    Workflow workflow = workflows.find("card_freeze", "2026.08.1").orElseThrow();
    assertThat(RouteQualityAssert.matches(evalCase.expected().stages(), workflow.stages()))
        .isTrue();

    List<WorkflowStage> broken = new ArrayList<>(workflow.stages());
    assertThat(broken.size()).isGreaterThanOrEqualTo(2);
    WorkflowStage first = broken.get(0);
    broken.set(0, broken.get(1));
    broken.set(1, first);

    assertThat(RouteQualityAssert.matches(evalCase.expected().stages(), broken)).isFalse();
  }
}
