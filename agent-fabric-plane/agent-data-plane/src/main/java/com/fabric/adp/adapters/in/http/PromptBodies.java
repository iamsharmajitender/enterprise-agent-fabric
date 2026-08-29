package com.fabric.adp.adapters.in.http;

import com.fabric.adp.domain.PromptPack;
import com.fabric.adp.domain.PromptRoleTemplate;
import java.util.LinkedHashMap;
import java.util.Map;

final class PromptBodies {

  private PromptBodies() {}

  static Map<String, Object> toBody(PromptPack pack) {
    if (pack == null) {
      return null;
    }
    Map<String, Object> byRole = new LinkedHashMap<>();
    for (PromptRoleTemplate role : pack.roles()) {
      Map<String, Object> template = new LinkedHashMap<>();
      template.put("task_type", role.taskType());
      template.put("text", role.text());
      byRole.put(role.llmRole(), template);
    }
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("prompt_id", pack.promptId());
    body.put("prompt_version", pack.promptVersion());
    body.put("host", pack.host());
    body.put("status", pack.status());
    body.put("owner", pack.owner());
    body.put("by_llm_role", byRole);
    return body;
  }
}
