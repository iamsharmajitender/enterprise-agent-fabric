package com.fabric.adp.application.eval;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record EvalExpected(String outcome, String routeId, String routeVersion) {}
