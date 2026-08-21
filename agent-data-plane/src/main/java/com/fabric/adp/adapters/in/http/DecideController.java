package com.fabric.adp.adapters.in.http;

import com.fabric.adp.application.DecideService;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class DecideController {

  private final DecideService decide;

  public DecideController(DecideService decide) {
    this.decide = decide;
  }

  @PostMapping("/v1/intent/decide")
  public Map<String, Object> decide(@RequestBody Map<String, Object> body, HttpServletRequest request) {
    String workload = (String) request.getAttribute(WorkloadAuthFilter.ATTR_WORKLOAD);
    @SuppressWarnings("unchecked")
    Map<String, Object> claims =
        body.get("claims") instanceof Map<?, ?> m ? (Map<String, Object>) m : Map.of();
    DecideResult result =
        decide.decide(
            new DecideRequest(
                string(body.get("ingress")),
                string(body.get("channel")),
                string(body.get("session_id")),
                string(body.get("message")),
                string(body.get("route_id")),
                claims),
            workload);
    Map<String, Object> response = new LinkedHashMap<>();
    response.put("outcome", result.outcome());
    response.put("intent_label", result.intentLabel());
    response.put("route_id", result.routeId());
    response.put("route_version", result.routeVersion());
    response.put("confidence", result.confidence());
    response.put("eligible_routes", result.eligibleRoutes());
    if (result.clarifyPrompt() != null) {
      response.put("clarify_prompt", result.clarifyPrompt());
    }
    if (result.candidates() != null) {
      response.put("candidates", result.candidates());
    }
    return response;
  }

  private static String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }
}
