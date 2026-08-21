package com.fabric.afd.domain;

public record EligibleRoute(
    String routeId, String routeVersion, String intentLabel, String description) {}
