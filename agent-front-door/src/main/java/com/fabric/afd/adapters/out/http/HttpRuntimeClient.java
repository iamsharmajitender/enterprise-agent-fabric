package com.fabric.afd.adapters.out.http;

import com.fabric.afd.application.RuntimePort;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.HydrateFailedException;
import com.fabric.afd.domain.NotFoundException;
import com.fabric.afd.domain.RunStart;
import com.fabric.afd.domain.UnavailableException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatusCode;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

public class HttpRuntimeClient implements RuntimePort {

  private static final Logger log = LoggerFactory.getLogger(HttpRuntimeClient.class);

  private static final ObjectMapper JSON = new ObjectMapper();

  private static final ParameterizedTypeReference<Map<String, Object>> MAP =
      new ParameterizedTypeReference<>() {};

  private final RestClient http;

  public HttpRuntimeClient(RestClient http) {
    this.http = http;
  }

  @Override
  public String start(RunStart start) {
    CatalogRoute route = start.route();
    Map<String, Object> contract = new LinkedHashMap<>();
    contract.put("tool_manifest", route.toolManifest());
    contract.put("manifest_version", route.toolManifestVersion());
    contract.put("policy_profile", route.policyProfile());
    contract.put("model_profile", route.modelProfile());
    contract.put("max_loop_steps", route.maxLoopSteps());
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("mode", "new");
    body.put("idempotency_key", start.idempotencyKey());
    body.put("session_id", start.sessionId());
    body.put("route_id", route.routeId());
    body.put("route_version", route.routeVersion());
    body.put("activation_target", route.activationTarget());
    body.put("agent_client_id", route.agentClientId());
    body.put("contract", contract);
    body.put("goal", start.payload());
    try {
      Map<String, Object> response = http.post().uri("/v1/runs").body(body).retrieve().body(MAP);
      if (response == null || response.get("correlation_id") == null) {
        throw new UnavailableException("runtime start unavailable");
      }
      return String.valueOf(response.get("correlation_id"));
    } catch (UnavailableException e) {
      throw e;
    } catch (RestClientResponseException e) {
      log.warn("runtime start failed status={} body={}", e.getStatusCode(), e.getResponseBodyAsString());
      if (e.getStatusCode().isSameCodeAs(HttpStatusCode.valueOf(422))) {
        throw new HydrateFailedException(runtimeErrorMessage(e));
      }
      throw new UnavailableException("runtime start unavailable", e);
    } catch (RestClientException e) {
      throw new UnavailableException("runtime start unavailable", e);
    }
  }

  @Override
  public Map<String, Object> status(String correlationId) {
    try {
      Map<String, Object> body =
          http.get().uri("/v1/runs/{id}", correlationId).retrieve().body(MAP);
      if (body == null) {
        throw new UnavailableException("runtime status unavailable");
      }
      return body;
    } catch (RestClientResponseException e) {
      if (e.getStatusCode().isSameCodeAs(HttpStatusCode.valueOf(404))) {
        throw new NotFoundException(correlationId);
      }
      throw new UnavailableException("runtime status unavailable", e);
    } catch (RestClientException e) {
      throw new UnavailableException("runtime status unavailable", e);
    }
  }

  @Override
  public void resume(String correlationId, String message) {
    try {
      http.post()
          .uri("/v1/runs/{id}/turns", correlationId)
          .body(Map.of("message", message == null ? "" : message))
          .retrieve()
          .toBodilessEntity();
    } catch (RestClientResponseException e) {
      if (e.getStatusCode().isSameCodeAs(HttpStatusCode.valueOf(404))) {
        throw new NotFoundException(correlationId);
      }
      throw new UnavailableException("runtime resume unavailable", e);
    } catch (RestClientException e) {
      throw new UnavailableException("runtime resume unavailable", e);
    }
  }

  @Override
  public Optional<FrozenRoute> openRun(String sessionId) {
    try {
      Map<String, Object> body =
          http.get()
              .uri(uri -> uri.path("/v1/runs").queryParam("session_id", sessionId).build())
              .retrieve()
              .body(MAP);
      if (body == null || body.containsKey("runs") || body.get("correlation_id") == null) {
        return Optional.empty();
      }
      String sid = string(body.get("session_id"));
      return Optional.of(
          new FrozenRoute(
              sid == null ? sessionId : sid,
              null,
              string(body.get("route_id")),
              string(body.get("route_version")),
              string(body.get("activation_target")),
              string(body.get("agent_client_id")),
              string(body.get("correlation_id"))));
    } catch (RestClientException e) {
      throw new UnavailableException("runtime open-run unavailable", e);
    }
  }

  private static String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }

  private static String runtimeErrorMessage(RestClientResponseException e) {
    try {
      JsonNode message = JSON.readTree(e.getResponseBodyAsString()).path("error").path("message");
      if (message.isTextual() && !message.asText().isBlank()) {
        return message.asText();
      }
    } catch (Exception ignored) {
      // fall through to a stable client-facing message
    }
    return "hydrate failed";
  }
}
