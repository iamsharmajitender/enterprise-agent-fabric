package com.fabric.registry.domain;

public record CapabilityVersion(
    String id,
    String version,
    String kind,
    String description,
    String inputSchemaJson,
    String outputSchemaJson,
    String invokeJson,
    String snippet,
    String owner,
    String status) {

  public boolean published() {
    return "published".equals(status);
  }

  public boolean draft() {
    return "draft".equals(status);
  }
}
