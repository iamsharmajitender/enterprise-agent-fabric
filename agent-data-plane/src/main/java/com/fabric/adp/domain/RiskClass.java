package com.fabric.adp.domain;

/**
 * Per-route decide bar for Layer ②. Mapped from {@link RouteRow#policyProfile()} — not a second
 * catalogue column. Unique keyword confidence is still {@code 0.91}; HIGH's bar sits above that so
 * a unique freeze/pay/write hit clarifies instead of silent {@code route}.
 */
public enum RiskClass {
  LOW(0.60),
  MID(0.85),
  HIGH(0.95);

  private final double routeBar;

  RiskClass(double routeBar) {
    this.routeBar = routeBar;
  }

  /** Minimum Layer ② confidence to {@code route}. Below this → {@code clarify}. */
  public double routeBar() {
    return routeBar;
  }

  public static RiskClass fromPolicy(String policyProfile) {
    if (policyProfile == null) {
      return MID;
    }
    return switch (policyProfile) {
      case "low_risk_chat" -> LOW;
      case "high_risk_step_up" -> HIGH;
      default -> MID;
    };
  }
}
