package com.fabric.adp.domain;

public record HealthStatus(String status) {

  public static HealthStatus up() {
    return new HealthStatus("UP");
  }
}
