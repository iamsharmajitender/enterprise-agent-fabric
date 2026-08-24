package com.fabric.adp.domain;

/** Catalogue-owned Layer ① rule. First match by {@code sortOrder} wins. */
public record IntentRule(
    String ruleId, String matchKind, String matchValue, String routeId, int sortOrder) {}
