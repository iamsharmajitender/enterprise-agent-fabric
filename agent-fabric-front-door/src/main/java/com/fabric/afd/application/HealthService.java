package com.fabric.afd.application;

import com.fabric.afd.domain.HealthStatus;

public class HealthService {

  public HealthStatus current() {
    return HealthStatus.up();
  }
}
