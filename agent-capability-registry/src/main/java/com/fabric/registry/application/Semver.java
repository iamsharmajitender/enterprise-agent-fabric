package com.fabric.registry.application;

final class Semver {

  private Semver() {}

  static int compare(String left, String right) {
    int[] a = parts(left);
    int[] b = parts(right);
    int n = Math.max(a.length, b.length);
    for (int i = 0; i < n; i++) {
      int av = i < a.length ? a[i] : 0;
      int bv = i < b.length ? b[i] : 0;
      int compared = Integer.compare(av, bv);
      if (compared != 0) {
        return compared;
      }
    }
    return 0;
  }

  private static int[] parts(String version) {
    if (version == null || version.isBlank()) {
      return new int[0];
    }
    String[] raw = version.split("\\.");
    int[] parsed = new int[raw.length];
    for (int i = 0; i < raw.length; i++) {
      try {
        parsed[i] = Integer.parseInt(raw[i]);
      } catch (NumberFormatException ignored) {
        parsed[i] = 0;
      }
    }
    return parsed;
  }
}
