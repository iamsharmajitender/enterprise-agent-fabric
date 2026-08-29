package com.fabric.adp.domain;

public record ManifestTool(
    String name,
    String capabilityId,
    String capabilityVersion,
    String pdpAction,
    String riskTier) {}
