package com.fabric.aadp.adapters.in.http;

import com.fabric.aadp.application.HealthService;
import com.fabric.aadp.domain.HealthStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

  private final HealthService healths;

  public HealthController(HealthService healths) {
    this.healths = healths;
  }

  @GetMapping("/health")
  public HealthStatus health() {
    return healths.current();
  }
}
