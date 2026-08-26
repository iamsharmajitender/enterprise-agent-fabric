package com.fabric.afd.domain;

import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Session freeze keys: {@code chat-|job-|sub-} + UUID. */
public final class SessionIds {
  private static final Pattern CHAT =
      Pattern.compile(
          "^chat-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$");
  /** Runtime mints {@code corr-} + 12 hex; idempotency is {@code subagent-{corr}-{stage_id}}. */
  private static final Pattern SUBAGENT_PARENT =
      Pattern.compile("^subagent-(corr-[0-9a-fA-F]{12})-(.+)$");

  private SessionIds() {}

  public static String mintChat() {
    return "chat-" + UUID.randomUUID();
  }

  /** Stable job/sub session from idempotency so retries keep the same freeze key. */
  public static String mintJobOrSub(String idempotencyKey) {
    String key = idempotencyKey == null ? "" : idempotencyKey.trim();
    String prefix = isSubagentKey(key) ? "sub" : "job";
    UUID id =
        UUID.nameUUIDFromBytes(("fabric-session:" + prefix + ":" + key).getBytes(StandardCharsets.UTF_8));
    return prefix + "-" + id;
  }

  public static boolean isChatSession(String sessionId) {
    return sessionId != null && CHAT.matcher(sessionId).matches();
  }

  public static boolean isSubagentKey(String idempotencyKey) {
    if (idempotencyKey == null) {
      return false;
    }
    String key = idempotencyKey.trim();
    return key.startsWith("subagent-") || key.startsWith("sub-");
  }

  /** Parent run id when this jobs start is a {@code kind=agent} child; otherwise null. */
  public static String parentCorrelationId(String idempotencyKey) {
    if (idempotencyKey == null) {
      return null;
    }
    Matcher m = SUBAGENT_PARENT.matcher(idempotencyKey.trim());
    return m.matches() ? m.group(1) : null;
  }
}
