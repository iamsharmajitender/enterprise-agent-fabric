package com.fabric.afd.adapters.in.http;

import com.fabric.afd.application.AssistantService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AssistantController {

  private final AssistantService assistant;

  public AssistantController(AssistantService assistant) {
    this.assistant = assistant;
  }

  @GetMapping("/v1/assistant/hints")
  public Map<String, Object> hints(
      @RequestParam(name = "session_id", required = false) String sessionId,
      HttpServletRequest request) {
    return assistant.hints(sessionId, claims(request));
  }

  @PostMapping("/v1/assistant/turns")
  public Map<String, Object> turn(@RequestBody Map<String, Object> body, HttpServletRequest request) {
    return assistant.turn(
        string(body.get("session_id")),
        string(body.get("message")),
        string(body.get("hint_id")),
        string(body.get("option_id")),
        claims(request));
  }

  @GetMapping("/v1/assistant/sessions/{sessionId}/events")
  public Map<String, Object> events(@PathVariable String sessionId) {
    return assistant.events(sessionId);
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> claims(HttpServletRequest request) {
    Object value = request.getAttribute(ChannelAuthFilter.ATTR_CLAIMS);
    return value instanceof Map<?, ?> map ? (Map<String, Object>) map : Map.of();
  }

  private static String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }
}
