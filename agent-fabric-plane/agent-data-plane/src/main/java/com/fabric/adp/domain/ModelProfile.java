package com.fabric.adp.domain;

public enum ModelProfile {
  REASONING_STANDARD("reasoning-standard"),
  FAST_CHAT("fast-chat"),
  LIGHTWEIGHT_CHAT("lightweight-chat");

  private final String id;

  ModelProfile(String id) {
    this.id = id;
  }

  public String id() {
    return id;
  }

  public static ModelProfile fromId(String id) {
    for (ModelProfile profile : values()) {
      if (profile.id.equals(id)) {
        return profile;
      }
    }
    throw new IllegalArgumentException("Unknown model_profile: " + id);
  }
}
