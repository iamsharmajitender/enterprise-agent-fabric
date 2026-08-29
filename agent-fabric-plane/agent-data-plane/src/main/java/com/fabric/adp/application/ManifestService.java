package com.fabric.adp.application;

import com.fabric.adp.domain.NotFoundException;
import com.fabric.adp.domain.ToolManifest;
import java.util.List;

public class ManifestService {

  private final ManifestStore store;

  public ManifestService(ManifestStore store) {
    this.store = store;
  }

  public ToolManifest get(String manifestId, String manifestVersion) {
    return store
        .find(manifestId, manifestVersion)
        .orElseThrow(() -> new NotFoundException(manifestId + "@" + manifestVersion));
  }

  public ToolManifest latest(String manifestId) {
    List<ToolManifest> found = store.listVersions(manifestId);
    if (found.isEmpty()) {
      throw new NotFoundException(manifestId);
    }
    return found.getFirst();
  }

  public List<ToolManifest> listLatest() {
    return store.listLatest();
  }

  public List<ToolManifest> listAll() {
    return store.listAll();
  }

  public List<ToolManifest> versions(String manifestId) {
    List<ToolManifest> found = store.listVersions(manifestId);
    if (found.isEmpty()) {
      throw new NotFoundException(manifestId);
    }
    return found;
  }
}
