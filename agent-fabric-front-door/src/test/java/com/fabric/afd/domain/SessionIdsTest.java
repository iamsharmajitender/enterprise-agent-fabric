package com.fabric.afd.domain;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class SessionIdsTest {

  @Test
  void mintChatUsesChatPrefixAndUuid() {
    String sid = SessionIds.mintChat();
    assertThat(sid).startsWith("chat-");
    assertThat(SessionIds.isChatSession(sid)).isTrue();
  }

  @Test
  void mintJobIsStableForIdempotencyKey() {
    String a = SessionIds.mintJobOrSub("job-fee-explain:v1");
    String b = SessionIds.mintJobOrSub("job-fee-explain:v1");
    assertThat(a).isEqualTo(b);
    assertThat(a).startsWith("job-");
  }

  @Test
  void mintSubagentUsesSubPrefix() {
    String sid = SessionIds.mintJobOrSub("subagent-corr-1-start_contract_review");
    assertThat(sid).startsWith("sub-");
    assertThat(SessionIds.mintJobOrSub("sub-corr-1-tool")).startsWith("sub-");
  }

  @Test
  void parentCorrelationIdFromSubagentKey() {
    String parent = "corr-550e8400-e29b-41d4-a716-446655440000";
    assertThat(SessionIds.parentCorrelationId("subagent-" + parent + "-start_contract_review"))
        .isEqualTo(parent);
    assertThat(SessionIds.parentCorrelationId("job-fee-explain:v1")).isNull();
    assertThat(SessionIds.parentCorrelationId("subagent-corr-1-start_contract_review")).isNull();
    assertThat(SessionIds.parentCorrelationId("subagent-corr-abcdef123456-start_contract_review"))
        .isNull();
  }
}
