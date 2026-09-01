package com.fabric.registry.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedCapabilitiesSqlTest {

  @Test
  void flywayBaselineIsSchemaOnly() throws Exception {
    String migration = readClasspath("/db/migration/V1__registry.sql");
    assertThat(migration).contains("CREATE TABLE registry.capabilities");
    assertThat(migration).doesNotContain("INSERT INTO registry.capabilities");
    assertThat(migration).doesNotContain("INSERT INTO registry.manifests");
  }

  @Test
  void catalogueSeedCoversShopassistManifestTools() throws Exception {
    String seed = readRoutePack("shopassist_case", "capability.sql");
    for (String id :
        new String[] {
          "lookup_order_by_order_id",
          "investigate_duplicate_charge",
          "check_return_policy",
          "escalate_to_human"
        }) {
      assertThat(seed).contains("'" + id + "'");
    }
    assertThat(seed).contains("x-ground-in-user-context");
    assertThat(seed).contains("^ORD-\\\\d+$");
    assertThat(readRoutePack("shopassist_case", "manifest.sql")).contains("'shopassist_case'");
    assertThat(seed).doesNotContain("'fee_explain'");
    assertThat(seed).doesNotContain("'web_search'");
  }

  @Test
  void catalogueSeedFeeExplainAccountIdPattern() throws Exception {
    String seed = readRoutePack("fee_explain", "capability.sql");
    assertThat(seed).contains("account_fee_lookup");
    assertThat(seed).contains("^acct-\\\\d+$");
    assertThat(seed).contains("x-ground-in-user-context");
  }

  private static String readClasspath(String path) throws Exception {
    try (var in = SeedCapabilitiesSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
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
