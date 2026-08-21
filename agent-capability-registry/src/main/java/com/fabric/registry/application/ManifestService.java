package com.fabric.registry.application;

import com.fabric.registry.domain.ManifestVersion;
import com.fabric.registry.domain.NotFoundException;
import com.fabric.registry.domain.PublishedConflictException;
import java.util.Optional;

public class ManifestService {

  private final ManifestStore store;

  public ManifestService(ManifestStore store) {
    this.store = store;
  }

  public ManifestVersion put(ManifestVersion incoming) {
    Optional<ManifestVersion> existing =
        store.find(incoming.manifestId(), incoming.manifestVersion());
    if (existing.isPresent() && existing.get().published()) {
      throw new PublishedConflictException(incoming.manifestId(), incoming.manifestVersion());
    }
    store.upsert(incoming);
    return incoming;
  }

  public ManifestVersion get(String manifestId, String manifestVersion, String workload) {
    ManifestVersion found =
        store
            .find(manifestId, manifestVersion)
            .orElseThrow(() -> new NotFoundException(manifestId + "@" + manifestVersion));
    if ("ar".equals(workload) && !found.published()) {
      throw new NotFoundException(manifestId + "@" + manifestVersion);
    }
    return found;
  }
}
