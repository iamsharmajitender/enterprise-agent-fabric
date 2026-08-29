package com.fabric.aadp.application;

import com.fabric.aadp.domain.HealthStatus;

public class HealthService {
  public HealthStatus current() {
    return HealthStatus.up();
  }
}
