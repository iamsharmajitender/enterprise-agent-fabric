package com.fabric.adp.adapters.in.http;

import com.fabric.adp.application.PromptService;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PromptController {

  private final PromptService prompts;

  public PromptController(PromptService prompts) {
    this.prompts = prompts;
  }

  @GetMapping("/v1/catalog/prompts")
  public Map<String, Object> list(
      @RequestParam(name = "include", required = false) String include) {
    List<Map<String, Object>> items =
        ("all".equals(include) ? prompts.listAll() : prompts.listPublished())
            .stream().map(PromptBodies::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("prompts", items);
    return body;
  }

  @GetMapping("/v1/catalog/prompts/{promptId}")
  public Map<String, Object> published(@PathVariable String promptId) {
    return PromptBodies.toBody(prompts.published(promptId));
  }

  @GetMapping("/v1/catalog/prompts/{promptId}/versions")
  public Map<String, Object> versions(@PathVariable String promptId) {
    List<Map<String, Object>> versions =
        prompts.versions(promptId).stream().map(PromptBodies::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("prompt_id", promptId);
    body.put("versions", versions);
    return body;
  }

  @GetMapping("/v1/catalog/prompts/{promptId}/versions/{promptVersion}")
  public Map<String, Object> get(
      @PathVariable String promptId, @PathVariable String promptVersion) {
    return PromptBodies.toBody(prompts.get(promptId, promptVersion));
  }
}
