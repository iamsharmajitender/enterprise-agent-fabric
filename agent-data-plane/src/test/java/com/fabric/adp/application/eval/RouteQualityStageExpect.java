package com.fabric.adp.application.eval;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record RouteQualityStageExpect(String id, String tool, String llmRole, String type) {}
