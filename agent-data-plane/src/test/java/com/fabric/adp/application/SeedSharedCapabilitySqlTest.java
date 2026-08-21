package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.springframework.util.StreamUtils;

class SeedSharedCapabilitySqlTest {

  @Test
  void flywaySeedAddsRoutesThatShareListAccounts() throws Exception {
    String seed = read("/db/migration/V12__seed_shared_capability_routes.sql");
    assertThat(seed).contains("'agent-balance-v1'");
    assertThat(seed).contains("'agent-statement-v1'");
    assertThat(seed).contains("'account-balance-v1'");
    assertThat(seed).contains("'account-statement-v1'");
    assertThat(count(seed, "\"capability_id\": \"list_accounts\"")).isEqualTo(2);
    assertThat(count(seed, "\"capability_id\": \"list_transactions\"")).isEqualTo(1);
  }

  private static int count(String haystack, String needle) {
    int n = 0;
    for (int from = 0; (from = haystack.indexOf(needle, from)) >= 0; from += needle.length()) {
      n++;
    }
    return n;
  }

  private static String read(String path) throws Exception {
    try (var in = SeedSharedCapabilitySqlTest.class.getResourceAsStream(path)) {
      assertThat(in).as(path).isNotNull();
      return StreamUtils.copyToString(in, StandardCharsets.UTF_8);
    }
  }
}
