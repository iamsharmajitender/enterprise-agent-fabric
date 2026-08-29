package com.fabric.adp.domain;

import java.util.List;

public record ToolManifest(
    String manifestId,
    String manifestVersion,
    String description,
    List<ManifestTool> tools,
    String status) {

  public ToolManifest(
      String manifestId, String manifestVersion, String description, List<ManifestTool> tools) {
    this(manifestId, manifestVersion, description, tools, "published");
  }
}
