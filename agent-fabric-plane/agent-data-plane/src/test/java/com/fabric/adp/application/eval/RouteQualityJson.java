package com.fabric.adp.application.eval;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Loads versioned route-quality suites from {@code agent-fabric-evals/route-quality/}. */
final class RouteQualityJson {

  static final ObjectMapper MAPPER =
      new ObjectMapper()
          .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
          .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

  private static final String ROOT = "/agent-fabric-evals/route-quality";

  private RouteQualityJson() {}

  /** Active suite_id → version (skips underscore keys such as {@code _comment}). */
  static Map<String, String> activeVersions() {
    JsonNode root = MAPPER.convertValue(loadRaw(ROOT + "/active.json"), JsonNode.class);
    Map<String, String> active = new LinkedHashMap<>();
    root.fields()
        .forEachRemaining(
            entry -> {
              if (entry.getKey().startsWith("_")) {
                return;
              }
              String version = entry.getValue().asText();
              if (version == null || version.isBlank()) {
                throw new IllegalStateException("active.json blank version for " + entry.getKey());
              }
              active.put(entry.getKey(), version);
            });
    if (active.isEmpty()) {
      throw new IllegalStateException("active.json has no suite entries");
    }
    return active;
  }

  static RouteQualityFile loadActive(String suiteId) {
    String version = activeVersions().get(suiteId);
    if (version == null) {
      throw new IllegalStateException("active.json missing suite " + suiteId);
    }
    return load(suiteId, version);
  }

  static RouteQualityFile load(String suiteId, String version) {
    String base = ROOT + "/routes/" + suiteId + "/" + version;
    RouteQualityFile file = readFile(base + "/cases.json");
    if (file.suiteId() != null && !suiteId.equals(file.suiteId())) {
      throw new IllegalStateException(
          "suite_id mismatch: " + suiteId + " vs cases " + file.suiteId());
    }
    if (file.suiteVersion() != null && !version.equals(file.suiteVersion())) {
      throw new IllegalStateException(
          "suite_version mismatch: " + version + " vs cases " + file.suiteVersion());
    }
    if (file.cases().isEmpty()) {
      throw new IllegalStateException(base + "/cases.json: cases required");
    }
    return new RouteQualityFile(suiteId, version, file.cases());
  }

  /** Every active suite’s cases, flattened for parameterized tests. */
  static List<LoadedCase> loadAllActiveCases() {
    List<LoadedCase> out = new ArrayList<>();
    for (Map.Entry<String, String> entry : activeVersions().entrySet()) {
      RouteQualityFile file = load(entry.getKey(), entry.getValue());
      for (RouteQualityCase evalCase : file.cases()) {
        out.add(new LoadedCase(entry.getKey(), entry.getValue(), evalCase));
      }
    }
    return out;
  }

  private static RouteQualityFile readFile(String classpath) {
    try (InputStream in = open(classpath)) {
      return MAPPER.readValue(in, RouteQualityFile.class);
    } catch (IOException e) {
      throw new UncheckedIOException(classpath, e);
    }
  }

  private static Object loadRaw(String classpath) {
    try (InputStream in = open(classpath)) {
      return MAPPER.readValue(in, Object.class);
    } catch (IOException e) {
      throw new UncheckedIOException(classpath, e);
    }
  }

  private static InputStream open(String classpath) {
    InputStream in = RouteQualityJson.class.getResourceAsStream(classpath);
    if (in == null) {
      throw new IllegalStateException("missing route-quality fixture: " + classpath);
    }
    return in;
  }

  record LoadedCase(String suiteId, String suiteVersion, RouteQualityCase evalCase) {}
}
