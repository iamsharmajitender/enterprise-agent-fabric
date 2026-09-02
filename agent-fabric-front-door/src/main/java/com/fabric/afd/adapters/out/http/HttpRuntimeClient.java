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
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
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

  private final RestClient.Builder clientTemplate;
  private final String defaultBaseUrl;
  private final List<String> knownBaseUrls;
  private final ConcurrentHashMap<String, RestClient> clientsByBase = new ConcurrentHashMap<>();

  public HttpRuntimeClient(
      RestClient.Builder clientTemplate, String defaultRuntimeUrl, String runtimeUrlsCsv) {
    this.clientTemplate = clientTemplate;
    this.defaultBaseUrl = normalizeBaseUrl(defaultRuntimeUrl);
    this.knownBaseUrls = parseKnownBaseUrls(defaultRuntimeUrl, runtimeUrlsCsv);
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
      Map<String, Object> response =
          client(route.activationTarget()).post().uri("/v1/runs").body(body).retrieve().body(MAP);
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
  public Map<String, Object> status(String correlationId, String activationTarget) {
    try {
      Map<String, Object> body =
          client(activationTarget).get().uri("/v1/runs/{id}", correlationId).retrieve().body(MAP);
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
  public void resume(String correlationId, String message, String activationTarget) {
    resumeTurn(correlationId, Map.of("message", message == null ? "" : message), activationTarget);
  }

  @Override
  public Map<String, Object> resumeTurn(
      String correlationId, Map<String, Object> body, String activationTarget) {
    try {
      Map<String, Object> response =
          client(activationTarget)
              .post()
              .uri("/v1/runs/{id}/turns", correlationId)
              .body(body == null ? Map.of() : body)
              .retrieve()
              .body(MAP);
      if (response == null) {
        throw new UnavailableException("runtime resume unavailable");
      }
      return response;
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
    for (String baseUrl : knownBaseUrls) {
      Optional<FrozenRoute> found = openRunOn(baseUrl, sessionId);
      if (found.isPresent()) {
        return found;
      }
    }
    return Optional.empty();
  }

  private Optional<FrozenRoute> openRunOn(String baseUrl, String sessionId) {
    try {
      Map<String, Object> body =
          clientForBase(baseUrl)
              .get()
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
    } catch (RestClientResponseException e) {
      if (e.getStatusCode().isSameCodeAs(HttpStatusCode.valueOf(404))) {
        return Optional.empty();
      }
      throw new UnavailableException("runtime open-run unavailable", e);
    } catch (RestClientException e) {
      throw new UnavailableException("runtime open-run unavailable", e);
    }
  }

  private RestClient client(String activationTarget) {
    return clientForBase(baseFor(activationTarget));
  }

  private RestClient clientForBase(String baseUrl) {
    return clientsByBase.computeIfAbsent(baseUrl, base -> clientTemplate.clone().baseUrl(base).build());
  }

  static String baseFor(String activationTarget, String defaultBaseUrl) {
    if (activationTarget == null || activationTarget.isBlank()) {
      return normalizeBaseUrl(defaultBaseUrl);
    }
    String trimmed = activationTarget.trim();
    int schemeEnd = trimmed.indexOf("://");
    if (schemeEnd < 0) {
      return normalizeBaseUrl(defaultBaseUrl);
    }
    int pathStart = trimmed.indexOf('/', schemeEnd + 3);
    if (pathStart < 0) {
      return stripTrailingSlash(trimmed);
    }
    return stripTrailingSlash(trimmed.substring(0, pathStart));
  }

  private String baseFor(String activationTarget) {
    return baseFor(activationTarget, defaultBaseUrl);
  }

  static List<String> parseKnownBaseUrls(String defaultRuntimeUrl, String runtimeUrlsCsv) {
    LinkedHashSet<String> bases = new LinkedHashSet<>();
    bases.add(normalizeBaseUrl(defaultRuntimeUrl));
    if (runtimeUrlsCsv != null && !runtimeUrlsCsv.isBlank()) {
      for (String entry : runtimeUrlsCsv.split(",")) {
        if (entry == null || entry.isBlank()) {
          continue;
        }
        String trimmed = entry.trim();
        if (trimmed.contains("://") && trimmed.indexOf('/', trimmed.indexOf("://") + 3) >= 0) {
          bases.add(baseFor(trimmed, defaultRuntimeUrl));
        } else {
          bases.add(normalizeBaseUrl(trimmed));
        }
      }
    }
    return List.copyOf(bases);
  }

  static String normalizeBaseUrl(String runtimeUrl) {
    if (runtimeUrl == null || runtimeUrl.isBlank()) {
      throw new IllegalArgumentException("runtime base url is required");
    }
    return baseFor(runtimeUrl, runtimeUrl);
  }

  private static String stripTrailingSlash(String value) {
    if (value == null || value.isEmpty()) {
      return value;
    }
    return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
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
