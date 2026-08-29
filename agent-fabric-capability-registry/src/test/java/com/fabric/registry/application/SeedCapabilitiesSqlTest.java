package com.fabric.registry.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedCapabilitiesSqlTest {

  @Test
  void flywayBaselineCoversShopassistManifestTools() throws Exception {
    String seed = read("/db/migration/V1__registry.sql");
    for (String id :
        new String[] {
          "lookup_order",
          "lookup_order_by_customer",
          "lookup_order_by_email",
          "investigate_duplicate_charge",
          "check_return_policy",
          "escalate_to_human"
        }) {
      assertThat(seed).contains("'" + id + "'");
    }
    assertThat(seed).contains("'shopassist_case'");
    assertThat(seed).doesNotContain("'fee_explain'");
    assertThat(seed).doesNotContain("'web_search'");
  }

  @Test
  void lookupOrderByEmailSchemaIsLocatorOnly() throws Exception {
    String seed = read("/db/migration/V1__registry.sql");
    int start = seed.indexOf("'lookup_order_by_email'");
    int end = seed.indexOf("'investigate_duplicate_charge'", start);
    assertThat(start).isGreaterThanOrEqualTo(0);
    assertThat(end).isGreaterThan(start);
    String block = seed.substring(start, end);
    assertThat(block).contains("\"email\"");
    assertThat(block).contains("\"required\":[\"email\"]");
    assertThat(block).doesNotContain("utterance");
  }

  private static String read(String path) throws Exception {
    try (var in = SeedCapabilitiesSqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }
}
