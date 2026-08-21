package com.fabric.afd.domain;

public record CatalogRoute(
    String routeId,
    String routeVersion,
    String activationTarget,
    String agentClientId,
    String toolManifest,
    String toolManifestVersion,
    String policyProfile,
    String modelProfile,
    Integer maxLoopSteps) {}
