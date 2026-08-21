package com.fabric.adp.application;

import com.fabric.adp.domain.HealthStatus;

public class HealthService {

  public HealthStatus current() {
    return HealthStatus.up();
  }
}
