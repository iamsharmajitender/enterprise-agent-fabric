package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedCatalogueSqlTest {

  @Test
  void flywayBaselineIsSchemaOnly() throws Exception {
    String migration = readClasspath("/db/migration/V1__dataplane.sql");
    assertThat(migration).contains("CREATE TABLE dataplane.routes");
    assertThat(migration).contains("dataplane.model_profiles");
    assertThat(migration).doesNotContain("INSERT INTO dataplane.routes");
    assertThat(migration).doesNotContain("INSERT INTO dataplane.manifests");
  }

  @Test
  void catalogueSeedContainsShopassistRoute() throws Exception {
    String route = readRoutePack("shopassist_case", "route.sql");
    String manifest = readRoutePack("shopassist_case", "manifest.sql");
    assertThat(route).contains("'shopassist_case'");
    assertThat(route).contains("autonomy_mode");
    assertThat(manifest).contains("lookup_order_by_order_id");
    assertThat(manifest).contains("escalate_to_human");
    assertThat(route).doesNotContain("'fee_explain'");
  }

  @Test
  void flywayIntentRulesIsSchemaOnly() throws Exception {
    String migration = readClasspath("/db/migration/V2__intent_rules.sql");
    assertThat(migration).contains("dataplane.intent_rules");
    assertThat(migration).doesNotContain("INSERT INTO dataplane.intent_rules");
  }

  @Test
  void catalogueSeedContainsIntentRules() throws Exception {
    String shopassist = readRoutePack("shopassist_case", "intent.sql");
    String overdraft = readRoutePack("overdraft_fee_qa", "intent.sql");
    assertThat(shopassist).contains("'shopassist_case'");
    assertThat(overdraft).contains("'overdraft_fee_qa'");
  }

  private static String readClasspath(String path) throws Exception {
    try (var in = SeedCatalogueSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }

  static String readRoutePackForTest(String routeId, String file) throws Exception {
    return readRoutePack(routeId, file);
  }

  private static String readRoutePack(String routeId, String file) throws Exception {
    Path path = catalogueSeedRoute(routeId, file);
    assertThat(path).as("catalogue-seed route pack").exists();
    return Files.readString(path, StandardCharsets.UTF_8);
  }

  private static Path catalogueSeedRoute(String routeId, String file) {
    Path dir = Path.of(System.getProperty("user.dir"));
    for (int i = 0; i < 6; i += 1) {
      Path candidate =
          dir.resolve("agent-fabric-scripts/catalogue-seed/route/" + routeId + "/" + file);
      if (Files.isRegularFile(candidate)) {
        return candidate;
      }
      if (dir.getParent() == null) {
        break;
      }
      dir = dir.getParent();
    }
    throw new IllegalStateException("missing catalogue-seed route pack: " + routeId + "/" + file);
  }
}
