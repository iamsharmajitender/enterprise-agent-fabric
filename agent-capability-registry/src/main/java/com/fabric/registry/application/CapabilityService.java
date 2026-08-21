package com.fabric.registry.application;

import com.fabric.registry.domain.CapabilityVersion;
import com.fabric.registry.domain.NotFoundException;
import com.fabric.registry.domain.PublishedConflictException;
import java.util.List;
import java.util.Optional;

public class CapabilityService {

  private final CapabilityStore store;

  public CapabilityService(CapabilityStore store) {
    this.store = store;
  }

  public CapabilityVersion put(CapabilityVersion incoming) {
    Optional<CapabilityVersion> existing = store.find(incoming.id(), incoming.version());
    if (existing.isPresent() && existing.get().published()) {
      throw new PublishedConflictException(incoming.id(), incoming.version());
    }
    store.upsert(incoming);
    return incoming;
  }

  public CapabilityVersion get(String id, String version, String workload) {
    CapabilityVersion found =
        store.find(id, version).orElseThrow(() -> new NotFoundException(id + "@" + version));
    if ("ar".equals(workload) && found.draft()) {
      throw new NotFoundException(id + "@" + version);
    }
    return found;
  }

  public List<CapabilityVersion> searchPublished(String query) {
    return store.listPublished(query == null ? "" : query);
  }

  public List<CapabilityVersion> listAll(String query) {
    return store.listAll(query == null ? "" : query);
  }

  public CapabilityVersion latest(String id, String workload) {
    return versions(id, workload).getFirst();
  }

  public CapabilityVersion latestPublished(String id) {
    return latest(id, "ar");
  }

  public List<CapabilityVersion> versions(String id, String workload) {
    List<CapabilityVersion> found = store.listVersions(id);
    if ("ar".equals(workload)) {
      found = found.stream().filter(row -> !row.draft()).toList();
    }
    if (found.isEmpty()) {
      throw new NotFoundException(id);
    }
    return found;
  }
}
