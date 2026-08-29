package com.fabric.afd.application;

import com.fabric.afd.domain.HealthStatus;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class HealthServiceTest {

  @Test
  void currentIsUp() {
    assertThat(new HealthService().current()).isEqualTo(HealthStatus.up());
  }
}
