package com.fabric.registry.domain;

public record ManifestVersion(
    String manifestId, String manifestVersion, String toolsJson, String status) {

  public boolean published() {
    return "published".equals(status);
  }

  public boolean draft() {
    return "draft".equals(status);
  }
}
