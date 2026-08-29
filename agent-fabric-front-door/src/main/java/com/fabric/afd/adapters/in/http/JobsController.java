package com.fabric.afd.adapters.in.http;

import com.fabric.afd.application.JobsService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class JobsController {

  private final JobsService jobs;

  public JobsController(JobsService jobs) {
    this.jobs = jobs;
  }

  @PostMapping("/v1/jobs")
  public ResponseEntity<Map<String, Object>> start(
      @RequestBody Map<String, Object> body, HttpServletRequest request) {
    @SuppressWarnings("unchecked")
    Map<String, Object> claims = (Map<String, Object>) request.getAttribute(ChannelAuthFilter.ATTR_CLAIMS);
    @SuppressWarnings("unchecked")
    Map<String, Object> payload =
        body.get("payload") instanceof Map<?, ?> m ? (Map<String, Object>) m : Map.of();
    String correlationId =
        jobs.start(string(body.get("route_id")), string(body.get("idempotency_key")), payload, claims);
    Map<String, Object> response = new LinkedHashMap<>();
    response.put("correlation_id", correlationId);
    return ResponseEntity.status(HttpStatus.ACCEPTED).body(response);
  }

  @GetMapping("/v1/jobs/{correlationId}")
  public Map<String, Object> status(@PathVariable String correlationId) {
    return jobs.status(correlationId);
  }

  private static String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }
}
