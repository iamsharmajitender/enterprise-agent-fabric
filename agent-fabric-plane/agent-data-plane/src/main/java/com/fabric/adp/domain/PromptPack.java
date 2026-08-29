package com.fabric.adp.domain;

import java.util.List;
import java.util.Optional;

public record PromptPack(
    String promptId,
    String promptVersion,
    String host,
    String status,
    String owner,
    List<PromptRoleTemplate> roles) {

  public PromptPack {
    roles = roles == null ? List.of() : List.copyOf(roles);
  }

  public Optional<PromptRoleTemplate> role(String llmRole) {
    if (llmRole == null || llmRole.isBlank() || "none".equals(llmRole)) {
      return Optional.empty();
    }
    return roles.stream().filter(role -> role.llmRole().equals(llmRole)).findFirst();
  }
}
