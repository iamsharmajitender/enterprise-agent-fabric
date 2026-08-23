package com.fabric.adp.application.eval;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.util.HashSet;
import java.util.Set;

final class EvalJson {

  static final ObjectMapper MAPPER =
      new ObjectMapper()
          .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
          .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

  private EvalJson() {}

  static EvalFile load(String classpath) {
    try (InputStream in = EvalJson.class.getResourceAsStream(classpath)) {
      if (in == null) {
        throw new IllegalStateException("missing eval fixture: " + classpath);
      }
      EvalFile file = MAPPER.readValue(in, EvalFile.class);
      Set<String> ids = new HashSet<>();
      for (EvalCase evalCase : file.cases()) {
        if (evalCase.id() == null || evalCase.id().isBlank()) {
          throw new IllegalStateException(classpath + ": case missing id");
        }
        if (!ids.add(evalCase.id())) {
          throw new IllegalStateException(classpath + ": duplicate case id " + evalCase.id());
        }
        if (evalCase.expected() == null || evalCase.expected().outcome() == null) {
          throw new IllegalStateException(evalCase.id() + ": expected.outcome required");
        }
      }
      return file;
    } catch (IOException e) {
      throw new UncheckedIOException(classpath, e);
    }
  }
}
