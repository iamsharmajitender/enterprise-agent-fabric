package com.fabric.afd.bootstrap;

import static org.assertj.core.api.Assertions.assertThat;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.sdk.resources.Resource;
import org.junit.jupiter.api.Test;

class StripTelemetrySdkResourceTest {

  @Test
  void dropsSdkResourceKeysAndKeepsServiceName() {
    Resource incoming = Resource.getDefault();
    assertThat(incoming.getAttribute(AttributeKey.stringKey("telemetry.sdk.language"))).isNotNull();

    Object out = new StripTelemetrySdkResource().postProcessAfterInitialization(incoming, "resource");

    assertThat(out).isInstanceOf(Resource.class);
    Resource stripped = (Resource) out;
    assertThat(stripped.getAttribute(AttributeKey.stringKey("telemetry.sdk.language"))).isNull();
    assertThat(stripped.getAttribute(AttributeKey.stringKey("telemetry.sdk.name"))).isNull();
    assertThat(stripped.getAttribute(AttributeKey.stringKey("telemetry.sdk.version"))).isNull();
    assertThat(stripped.getAttribute(AttributeKey.stringKey("telemetry.auto.version"))).isNull();
    assertThat(stripped.getAttribute(AttributeKey.stringKey("service.name"))).isNotNull();
  }
}
