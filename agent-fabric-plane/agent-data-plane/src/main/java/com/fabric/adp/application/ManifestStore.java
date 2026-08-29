package com.fabric.adp.application;

import com.fabric.adp.domain.ToolManifest;
import java.util.List;
import java.util.Optional;

public interface ManifestStore {

  Optional<ToolManifest> find(String manifestId, String manifestVersion);

  List<ToolManifest> listLatest();

  List<ToolManifest> listAll();

  List<ToolManifest> listVersions(String manifestId);
}
