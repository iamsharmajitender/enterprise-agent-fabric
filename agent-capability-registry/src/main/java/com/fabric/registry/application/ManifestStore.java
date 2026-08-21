package com.fabric.registry.application;

import com.fabric.registry.domain.ManifestVersion;
import java.util.Optional;

public interface ManifestStore {

  Optional<ManifestVersion> find(String manifestId, String manifestVersion);

  void upsert(ManifestVersion manifest);
}
