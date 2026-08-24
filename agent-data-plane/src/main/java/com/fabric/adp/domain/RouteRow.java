package com.fabric.adp.domain;

import java.util.List;

public record RouteRow(
    String routeId,
    String routeVersion,
    boolean active,
    String intentLabel,
    String description,
    String activationTarget,
    String agentClientId,
    ToolManifest manifest,
    String policyProfile,
    ModelProfile modelProfile,
    Retrieval retrieval,
    MemoryProfile memoryProfile,
    String workflowId,
    String promptId,
    String outputSchemaId,
    String evalSuiteId,
    Integer maxLoopSteps,
    String fallback,
    List<String> requiredClaims,
    List<String> channels,
    boolean chatVisible,
    List<String> keywords,
    AutonomyPattern autonomyMode,
    String status) {

  public RouteRow(
      String routeId,
      String routeVersion,
      boolean active,
      String intentLabel,
      String description,
      String activationTarget,
      String agentClientId,
      ToolManifest manifest,
      String policyProfile,
      ModelProfile modelProfile,
      Retrieval retrieval,
      MemoryProfile memoryProfile,
      String workflowId,
      String promptId,
      String outputSchemaId,
      String evalSuiteId,
      Integer maxLoopSteps,
      String fallback,
      List<String> requiredClaims,
      List<String> channels,
      boolean chatVisible,
      List<String> keywords,
      AutonomyPattern autonomyMode) {
    this(
        routeId,
        routeVersion,
        active,
        intentLabel,
        description,
        activationTarget,
        agentClientId,
        manifest,
        policyProfile,
        modelProfile,
        retrieval,
        memoryProfile,
        workflowId,
        promptId,
        outputSchemaId,
        evalSuiteId,
        maxLoopSteps,
        fallback,
        requiredClaims,
        channels,
        chatVisible,
        keywords,
        autonomyMode,
        active ? "active" : "published");
  }

  public RiskClass riskClass() {
    return RiskClass.fromPolicy(policyProfile);
  }
}
