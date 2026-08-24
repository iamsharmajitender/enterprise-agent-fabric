package com.fabric.adp.domain;

import java.util.List;

public record Retrieval(String mode, List<String> scope) {

  public static Retrieval fromMode(String mode, List<String> scope) {
    return hasMode(mode) ? new Retrieval(mode, scope) : null;
  }

  public static boolean hasMode(String mode) {
    if (mode == null || mode.isBlank()) {
      return false;
    }
    String normalized = mode.trim();
    return !"none".equalsIgnoreCase(normalized) && !"omit".equalsIgnoreCase(normalized);
  }
}
