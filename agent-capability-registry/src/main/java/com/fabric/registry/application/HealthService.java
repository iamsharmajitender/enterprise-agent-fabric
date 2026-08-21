package com.fabric.registry.application;

import com.fabric.registry.domain.HealthStatus;

public class HealthService {

  public HealthStatus current() {
    return HealthStatus.up();
  }
}
