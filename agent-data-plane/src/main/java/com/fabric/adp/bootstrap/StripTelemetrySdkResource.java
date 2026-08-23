package com.fabric.adp.bootstrap;

import io.opentelemetry.sdk.resources.Resource;
import java.util.Set;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.stereotype.Component;

/**
 * Drop telemetry.sdk.* from the Spring OpenTelemetry {@link Resource} so traces, logs, and
 * Micrometer OTLP metrics do not carry SDK language/name/version labels.
 */
@Component
class StripTelemetrySdkResource implements BeanPostProcessor {

  private static final Set<String> DROP =
      Set.of(
          "telemetry.sdk.language",
          "telemetry.sdk.name",
          "telemetry.sdk.version",
          "telemetry.auto.version");

  @Override
  public Object postProcessAfterInitialization(Object bean, String beanName) throws BeansException {
    if (!(bean instanceof Resource resource)) {
      return bean;
    }
    return resource.toBuilder().removeIf(key -> DROP.contains(key.getKey())).build();
  }
}
