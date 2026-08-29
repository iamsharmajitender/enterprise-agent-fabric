package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedCatalogueSqlTest {

  @Test
  void flywayBaselineContainsShopassistRoute() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("'shopassist_case'");
    assertThat(seed).contains("lookup_order");
    assertThat(seed).contains("escalate_to_human");
    assertThat(seed).contains("autonomy_mode");
    assertThat(seed).doesNotContain("'fee_explain'");
    assertThat(seed).doesNotContain("'web_search'");
  }

  @Test
  void flywayIntentRulesSeedSlashCommands() throws Exception {
    String seed = read("/db/migration/V2__intent_rules.sql");
    assertThat(seed).contains("dataplane.intent_rules");
    assertThat(seed).contains("'shopassist_case'");
  }

  private static String read(String path) throws Exception {
    try (var in = SeedCatalogueSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }
}
