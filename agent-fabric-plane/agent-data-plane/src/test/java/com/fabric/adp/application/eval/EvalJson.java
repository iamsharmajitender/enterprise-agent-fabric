package com.fabric.adp.application.eval;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

final class EvalJson {

  static final ObjectMapper MAPPER =
      new ObjectMapper()
          .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
          .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

  private static final String ROOT = "/agent-fabric-evals/intent-router-evals";

  private EvalJson() {}

  /** Load the active version of a suite (`routing`, `jobs-entitle`, …) from intent-router-evals. */
  static EvalFile loadActive(String suiteId) {
    String version = activeVersion(suiteId);
    String base = ROOT + "/" + suiteId + "/" + version;
    String prefix = filePrefix(suiteId);
    String manifestPath = base + "/" + prefix + "-case-manifest.json";
    EvalFile file =
        resourceExists(manifestPath)
            ? loadSplit(suiteId, version, base, prefix)
            : load(base + "/cases.json");
    if (file.suiteId() != null && !suiteId.equals(file.suiteId())) {
      throw new IllegalStateException(
          "suite_id mismatch: active " + suiteId + " vs cases " + file.suiteId());
    }
    if (file.suiteVersion() != null && !version.equals(file.suiteVersion())) {
      throw new IllegalStateException(
          "suite_version mismatch: active "
              + version
              + " vs cases "
              + file.suiteVersion()
              + " for "
              + suiteId);
    }
    return file;
  }

  /**
   * On-disk filename stem for suite artifacts ({@code *-suite.json}, {@code *-catalogue.json},
   * {@code *-case-manifest.json}). Folder name stays the suite id; routing uses {@code route-} for
   * brevity.
   */
  static String filePrefix(String suiteId) {
    return switch (suiteId) {
      case "routing" -> "route";
      default -> suiteId;
    };
  }

  static String activeVersion(String suiteId) {
    @SuppressWarnings("unchecked")
    Map<String, String> active = MAPPER.convertValue(loadRaw(ROOT + "/active.json"), Map.class);
    String version = active.get(suiteId);
    if (version == null || version.isBlank()) {
      throw new IllegalStateException("active.json missing suite " + suiteId);
    }
    return version;
  }

  /** Multi-file suite: {prefix}-catalogue.json + {prefix}-case-manifest.json + cases/*.json. */
  private static EvalFile loadSplit(String suiteId, String version, String base, String prefix) {
    String cataloguePath = base + "/" + prefix + "-catalogue.json";
    String manifestPath = base + "/" + prefix + "-case-manifest.json";

    JsonNode catalogueRoot = MAPPER.convertValue(loadRaw(cataloguePath), JsonNode.class);
    List<EvalCataloguePin> catalogue =
        MAPPER.convertValue(
            catalogueRoot.get("catalogue"),
            MAPPER.getTypeFactory().constructCollectionType(List.class, EvalCataloguePin.class));
    if (catalogue == null) {
      catalogue = List.of();
    }

    JsonNode manifest = MAPPER.convertValue(loadRaw(manifestPath), JsonNode.class);
    JsonNode files = manifest.get("case_files");
    if (files == null || !files.isArray() || files.isEmpty()) {
      throw new IllegalStateException(manifestPath + ": case_files required");
    }

    List<EvalCase> cases = new ArrayList<>();
    Set<String> ids = new HashSet<>();
    for (JsonNode fileNameNode : files) {
      String fileName = fileNameNode.asText();
      String path = base + "/cases/" + fileName;
      JsonNode fragment = MAPPER.convertValue(loadRaw(path), JsonNode.class);
      JsonNode caseNodes = fragment.get("cases");
      if (caseNodes == null || !caseNodes.isArray()) {
        throw new IllegalStateException(path + ": cases array required");
      }
      for (JsonNode caseNode : caseNodes) {
        EvalCase evalCase = MAPPER.convertValue(caseNode, EvalCase.class);
        validateCase(path, evalCase, ids);
        cases.add(evalCase);
      }
    }
    return new EvalFile(suiteId, version, catalogue, cases);
  }

  static EvalFile load(String classpath) {
    try (InputStream in = open(classpath)) {
      EvalFile file = MAPPER.readValue(in, EvalFile.class);
      Set<String> ids = new HashSet<>();
      for (EvalCase evalCase : file.cases()) {
        validateCase(classpath, evalCase, ids);
      }
      return file;
    } catch (IOException e) {
      throw new UncheckedIOException(classpath, e);
    }
  }

  private static void validateCase(String source, EvalCase evalCase, Set<String> ids) {
    if (evalCase.id() == null || evalCase.id().isBlank()) {
      throw new IllegalStateException(source + ": case missing id");
    }
    if (!ids.add(evalCase.id())) {
      throw new IllegalStateException(source + ": duplicate case id " + evalCase.id());
    }
    if (evalCase.expected() == null || evalCase.expected().outcome() == null) {
      throw new IllegalStateException(evalCase.id() + ": expected.outcome required");
    }
  }

  private static boolean resourceExists(String classpath) {
    return EvalJson.class.getResource(classpath) != null;
  }

  private static Object loadRaw(String classpath) {
    try (InputStream in = open(classpath)) {
      return MAPPER.readValue(in, Object.class);
    } catch (IOException e) {
      throw new UncheckedIOException(classpath, e);
    }
  }

  private static InputStream open(String classpath) {
    InputStream in = EvalJson.class.getResourceAsStream(classpath);
    if (in == null) {
      throw new IllegalStateException("missing eval fixture: " + classpath);
    }
    return in;
  }
}
