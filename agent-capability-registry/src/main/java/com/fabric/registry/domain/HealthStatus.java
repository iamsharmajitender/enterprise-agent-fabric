package com.fabric.registry.domain;

public record HealthStatus(String status) {

  public static HealthStatus up() {
    return new HealthStatus("UP");
  }
}
