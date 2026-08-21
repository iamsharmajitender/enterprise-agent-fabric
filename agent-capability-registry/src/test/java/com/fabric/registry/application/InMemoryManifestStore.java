package com.fabric.registry.application;

import com.fabric.registry.domain.ManifestVersion;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

public class InMemoryManifestStore implements ManifestStore {

  private final ConcurrentHashMap<String, ManifestVersion> rows = new ConcurrentHashMap<>();

  @Override
  public Optional<ManifestVersion> find(String manifestId, String manifestVersion) {
    return Optional.ofNullable(rows.get(key(manifestId, manifestVersion)));
  }

  @Override
  public void upsert(ManifestVersion manifest) {
    rows.put(key(manifest.manifestId(), manifest.manifestVersion()), manifest);
  }

  private static String key(String manifestId, String manifestVersion) {
    return manifestId + "@" + manifestVersion;
  }
}
