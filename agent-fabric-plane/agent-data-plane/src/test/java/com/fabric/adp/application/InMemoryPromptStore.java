package com.fabric.adp.application;

import com.fabric.adp.domain.PromptPack;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class InMemoryPromptStore implements PromptStore {

  private final Map<String, PromptPack> rows = new LinkedHashMap<>();

  public InMemoryPromptStore seedDemo() {
    put(shopassistCase());
    return this;
  }

  public static PromptPack shopassistCase() {
    return new PromptPack(
        "shopassist_case",
        "2026.08.1",
        "Pattern 1. You are ShopAssist front-line support. Reply CALL <tool_id>, ASK <question>, or DONE <answer>.",
        "published",
        "shopassist",
        List.of());
  }

  private void put(PromptPack pack) {
    rows.put(key(pack.promptId(), pack.promptVersion()), pack);
  }

  @Override
  public Optional<PromptPack> find(String promptId, String promptVersion) {
    return Optional.ofNullable(rows.get(key(promptId, promptVersion)));
  }

  @Override
  public Optional<PromptPack> findPublished(String promptId) {
    return rows.values().stream()
        .filter(pack -> pack.promptId().equals(promptId) && "published".equals(pack.status()))
        .max((a, b) -> CatalogVersion.compare(a.promptVersion(), b.promptVersion()));
  }

  @Override
  public List<PromptPack> listPublished() {
    Map<String, PromptPack> latest = new LinkedHashMap<>();
    for (PromptPack pack : rows.values()) {
      if (!"published".equals(pack.status())) {
        continue;
      }
      PromptPack existing = latest.get(pack.promptId());
      if (existing == null
          || CatalogVersion.compare(pack.promptVersion(), existing.promptVersion()) > 0) {
        latest.put(pack.promptId(), pack);
      }
    }
    return latest.values().stream().sorted(Comparator.comparing(PromptPack::promptId)).toList();
  }

  @Override
  public List<PromptPack> listAll() {
    return rows.values().stream()
        .sorted(
            Comparator.comparing(PromptPack::promptId)
                .thenComparing((a, b) -> CatalogVersion.compare(b.promptVersion(), a.promptVersion())))
        .toList();
  }

  @Override
  public List<PromptPack> listVersions(String promptId) {
    return rows.values().stream()
        .filter(pack -> pack.promptId().equals(promptId))
        .sorted((a, b) -> CatalogVersion.compare(b.promptVersion(), a.promptVersion()))
        .toList();
  }

  private static String key(String promptId, String promptVersion) {
    return promptId + "@" + promptVersion;
  }
}
