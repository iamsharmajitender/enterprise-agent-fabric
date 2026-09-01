package com.fabric.adp.adapters.in.http;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.HashSet;
import java.util.Set;

final class StubClaims {

  private StubClaims() {}

  static Set<String> entitled(String header, ObjectMapper mapper) {
    if (header == null || header.isBlank()) {
      return Set.of();
    }
    try {
      JsonNode emts = mapper.readTree(header).path("emts");
      Set<String> claims = new HashSet<>();
      emts.properties()
          .forEach(
              e -> {
                if (e.getValue().asBoolean()) {
                  claims.add(e.getKey());
                }
              });
      return claims;
    } catch (Exception e) {
      return Set.of();
    }
  }
}
