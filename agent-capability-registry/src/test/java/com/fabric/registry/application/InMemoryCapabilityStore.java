package com.fabric.registry.application;

import com.fabric.registry.domain.CapabilityVersion;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

public class InMemoryCapabilityStore implements CapabilityStore {

  private final ConcurrentHashMap<String, CapabilityVersion> rows = new ConcurrentHashMap<>();

  @Override
  public Optional<CapabilityVersion> find(String id, String version) {
    return Optional.ofNullable(rows.get(key(id, version)));
  }

  @Override
  public void upsert(CapabilityVersion capability) {
    rows.put(key(capability.id(), capability.version()), capability);
  }

  @Override
  public List<CapabilityVersion> listPublished(String query) {
    String needle = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
    Map<String, CapabilityVersion> latest = new HashMap<>();
    for (CapabilityVersion row : rows.values()) {
      if (!row.published()) {
        continue;
      }
      CapabilityVersion existing = latest.get(row.id());
      if (existing == null || Semver.compare(row.version(), existing.version()) > 0) {
        latest.put(row.id(), row);
      }
    }
    return latest.values().stream()
        .filter(row -> matches(row, needle))
        .sorted(Comparator.comparing(CapabilityVersion::id))
        .toList();
  }

  @Override
  public List<CapabilityVersion> listAll(String query) {
    String needle = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
    return rows.values().stream()
        .filter(row -> matches(row, needle))
        .sorted(
            Comparator.comparing(CapabilityVersion::id)
                .thenComparing((a, b) -> Semver.compare(b.version(), a.version())))
        .toList();
  }

  @Override
  public List<CapabilityVersion> listVersions(String id) {
    return rows.values().stream()
        .filter(row -> row.id().equals(id))
        .sorted((a, b) -> Semver.compare(b.version(), a.version()))
        .toList();
  }

  private static boolean matches(CapabilityVersion row, String needle) {
    if (needle.isEmpty()) {
      return true;
    }
    if (row.id().toLowerCase(Locale.ROOT).contains(needle)) {
      return true;
    }
    return row.description() != null && row.description().toLowerCase(Locale.ROOT).contains(needle);
  }

  private static String key(String id, String version) {
    return id + "@" + version;
  }
}
