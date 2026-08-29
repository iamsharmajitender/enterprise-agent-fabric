package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedChatHiddenRoutesSqlTest {

  @Test
  void flywayBaselineIncludesShopassistChatRoute() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("'shopassist_case'");
    assertThat(seed).contains("TRUE");
    assertThat(seed).contains("support:case");
    assertThat(seed).doesNotContain("'fee_explain'");
    assertThat(seed).doesNotContain("'email_summarize'");
  }

  @Test
  void flywayBaselineIncludesWorkflowTable() throws Exception {
    String seed = read("/db/migration/V1__dataplane.sql");
    assertThat(seed).contains("CREATE TABLE dataplane.workflows");
    assertThat(seed).contains("CREATE TABLE dataplane.corpora");
  }

  private static String read(String path) throws Exception {
    try (var in = SeedChatHiddenRoutesSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }
}
