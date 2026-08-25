package com.fabric.adp.application.eval;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.domain.WorkflowStage;
import java.util.List;
import java.util.Objects;

/** Compares fixture {@code expected.stages} to a seeded workflow stage list. */
final class RouteQualityAssert {

  private RouteQualityAssert() {}

  static void assertStageOrder(
      String caseId, List<RouteQualityStageExpect> expected, List<WorkflowStage> actual) {
    assertThat(expected).as("%s: expected.stages required", caseId).isNotEmpty();
    assertThat(actual)
        .as("%s: workflow stage count (expected %s)", caseId, summarize(expected))
        .hasSize(expected.size());
    for (int i = 0; i < expected.size(); i++) {
      RouteQualityStageExpect want = expected.get(i);
      WorkflowStage got = actual.get(i);
      assertThat(got.id())
          .as("%s: stage[%d].id", caseId, i)
          .isEqualTo(want.id());
      if (want.tool() != null && !want.tool().isBlank()) {
        assertThat(got.tool())
            .as("%s: stage[%d].tool (%s)", caseId, i, want.id())
            .isEqualTo(want.tool());
      }
      if (want.llmRole() != null && !want.llmRole().isBlank()) {
        assertThat(normalize(got.llmRole()))
            .as("%s: stage[%d].llm_role (%s)", caseId, i, want.id())
            .isEqualTo(want.llmRole());
      }
      if (want.type() != null && !want.type().isBlank()) {
        assertThat(got.type())
            .as("%s: stage[%d].type (%s)", caseId, i, want.id())
            .isEqualTo(want.type());
      }
    }
  }

  static boolean matches(List<RouteQualityStageExpect> expected, List<WorkflowStage> actual) {
    if (expected == null || expected.isEmpty() || actual == null || expected.size() != actual.size()) {
      return false;
    }
    for (int i = 0; i < expected.size(); i++) {
      RouteQualityStageExpect want = expected.get(i);
      WorkflowStage got = actual.get(i);
      if (!Objects.equals(want.id(), got.id())) {
        return false;
      }
      if (want.tool() != null && !want.tool().isBlank() && !want.tool().equals(got.tool())) {
        return false;
      }
      if (want.llmRole() != null
          && !want.llmRole().isBlank()
          && !want.llmRole().equals(normalize(got.llmRole()))) {
        return false;
      }
      if (want.type() != null && !want.type().isBlank() && !want.type().equals(got.type())) {
        return false;
      }
    }
    return true;
  }

  private static String normalize(String llmRole) {
    return llmRole == null || llmRole.isBlank() ? "none" : llmRole;
  }

  private static String summarize(List<RouteQualityStageExpect> expected) {
    return expected.stream().map(RouteQualityStageExpect::id).toList().toString();
  }
}
