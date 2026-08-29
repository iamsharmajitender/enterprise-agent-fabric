package com.fabric.registry.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fabric.registry.domain.ManifestVersion;
import com.fabric.registry.domain.NotFoundException;
import com.fabric.registry.domain.PublishedConflictException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.InputStream;
import org.junit.jupiter.api.Test;

class ManifestServiceTest {

  @Test
  void publishesFixtureAndRejectsOverwrite() throws Exception {
    ManifestService service = new ManifestService(new InMemoryManifestStore());
    ObjectMapper mapper = new ObjectMapper();
    try (InputStream in = getClass().getResourceAsStream("/contracts/manifest-fee-explain.json")) {
      var tree = mapper.readTree(in);
      ManifestVersion published =
          new ManifestVersion(
              tree.get("manifest_id").asText(),
              tree.get("manifest_version").asText(),
              mapper.writeValueAsString(tree.get("tools")),
              "published");
      service.put(published);
      assertThat(service.get("fee_explain_v1", "2026.08.1", "ar").published()).isTrue();
      assertThatThrownBy(() -> service.put(published)).isInstanceOf(PublishedConflictException.class);
    }
  }

  @Test
  void missingVersionIsNotFound() {
    ManifestService service = new ManifestService(new InMemoryManifestStore());
    assertThatThrownBy(() -> service.get("fee_explain_v1", "latest", "ar"))
        .isInstanceOf(NotFoundException.class);
  }
}
