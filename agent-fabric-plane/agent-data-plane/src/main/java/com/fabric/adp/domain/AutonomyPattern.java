package com.fabric.adp.domain;

public enum AutonomyPattern {
  SINGLE_INFERENCE(0),
  AUTONOMOUS(1),
  DETERMINISTIC(2),
  GUIDED(3);

  private final int code;

  AutonomyPattern(int code) {
    this.code = code;
  }

  public int code() {
    return code;
  }

  public static AutonomyPattern fromCode(int code) {
    for (AutonomyPattern mode : values()) {
      if (mode.code == code) {
        return mode;
      }
    }
    throw new IllegalArgumentException("Unknown autonomy_mode: " + code);
  }
}
