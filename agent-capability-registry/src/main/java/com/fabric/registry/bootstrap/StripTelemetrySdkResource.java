package com.fabric.registry.bootstrap;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.sdk.resources.Resource;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.stereotype.Component;

/**
 * Drop telemetry.sdk.* from the Spring OpenTelemetry {@link Resource} so traces, logs, and
 * Micrometer OTLP metrics do not carry SDK language/name/version labels.
 */
@Component
class StripTelemetrySdkResource implements BeanPostProcessor {

  private static final String[] DROP = {
    "telemetry.sdk.language",
    "telemetry.sdk.name",
    "telemetry.sdk.version",
    "telemetry.auto.version"
  };

  @Override
  public Object postProcessAfterInitialization(Object bean, String beanName) throws BeansException {
    if (!(bean instanceof Resource resource)) {
      return bean;
    }
    var builder = resource.toBuilder();
    for (String key : DROP) {
      builder.removeAttribute(AttributeKey.stringKey(key));
    }
    return builder.build();
  }
}
