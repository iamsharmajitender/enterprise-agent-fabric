package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.domain.AutonomyPattern;
import com.fabric.adp.domain.MemoryProfile;
import com.fabric.adp.domain.ModelProfile;
import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;

class CatalogueServiceTest {

  private final CatalogueService catalogue =
      new CatalogueService(new InMemoryRouteStore().seedDemo());

  @Test
  void listAllIsTheCatalogueSeed() {
    assertThat(catalogue.list()).extracting(RouteRow::routeId).containsExactly("shopassist_case");
    assertThat(catalogue.listAll()).hasSize(1);
  }

  @Test
  void janeSeesShopassistOnWebWithSupportClaim() {
    var eligible = catalogue.eligible("web", Set.of("support:case"));
    assertThat(eligible).extracting(RouteRow::routeId).containsExactly("shopassist_case");
  }

  @Test
  void shopassistCaseIsPatternOneAutonomous() {
    RouteRow row = catalogue.get("shopassist_case", "2026.08.1");
    assertThat(row.manifest().manifestId()).isEqualTo("shopassist_case");
    assertThat(row.autonomyMode()).isEqualTo(AutonomyPattern.AUTONOMOUS);
    assertThat(row.activationTarget()).isEqualTo("http://agent-runtime:3008/v1/runs");
    assertThat(row.promptId()).isEqualTo("shopassist_case");
    assertThat(row.modelProfile()).isEqualTo(ModelProfile.REASONING_STANDARD);
    assertThat(row.retrieval()).isNull();
    assertThat(row.memoryProfile()).isEqualTo(
        new MemoryProfile(
            "session", "session", "checkpoint", "none", 24,
            List.of("tenant", "user", "session")));
    assertThat(row.chatVisible()).isTrue();
    assertThat(row.requiredClaims()).containsExactly("support:case");
  }

  @Test
  void shopassistHasASingleActiveVersion() {
    assertThat(catalogue.versions("shopassist_case")).extracting(RouteRow::routeVersion)
        .containsExactly("2026.08.1");
  }
}
