package com.fabric.afd.domain;

public record HealthStatus(String status) {

  public static HealthStatus up() {
    return new HealthStatus("UP");
  }
}
