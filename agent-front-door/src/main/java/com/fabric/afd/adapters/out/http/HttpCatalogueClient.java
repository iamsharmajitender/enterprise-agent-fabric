package com.fabric.afd.adapters.out.http;

import com.fabric.afd.application.CataloguePort;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.EligibleRoute;
import com.fabric.afd.domain.UnavailableException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

public class HttpCatalogueClient implements CataloguePort {

  private static final ParameterizedTypeReference<Map<String, Object>> MAP =
      new ParameterizedTypeReference<>() {};

  private final RestClient http;
  private final ObjectMapper mapper;

  public HttpCatalogueClient(RestClient http, ObjectMapper mapper) {
    this.http = http;
    this.mapper = mapper;
  }

  @Override
  public CatalogRoute get(String routeId, String routeVersion) {
    try {
      Map<String, Object> body =
          http.get()
              .uri(
                  uri ->
                      uri.path("/v1/catalog/routes/{routeId}")
                          .queryParam("route_version", routeVersion)
                          .build(routeId))
              .retrieve()
              .body(MAP);
      if (body == null || body.get("route_id") == null) {
        throw new UnavailableException("catalogue unavailable");
      }
      return new CatalogRoute(
          string(body.get("route_id")),
          string(body.get("route_version")),
          string(body.get("activation_target")),
          string(body.get("agent_client_id")),
          string(body.get("tool_manifest")),
          string(body.get("tool_manifest_version")),
          string(body.get("policy_profile")),
          string(body.get("model_profile")),
          integer(body.get("max_loop_steps")));
    } catch (UnavailableException e) {
      throw e;
    } catch (RestClientException e) {
      throw new UnavailableException("catalogue unavailable", e);
    }
  }

  @Override
  public List<EligibleRoute> eligible(String channel, Map<String, Object> claims) {
    try {
      String claimsJson = mapper.writeValueAsString(claims == null ? Map.of() : claims);
      Map<String, Object> body =
          http.get()
              .uri(
                  uri ->
                      uri.path("/v1/intent/eligible")
                          .queryParam("channel", channel)
                          .build())
              .header("X-Stub-Claims", claimsJson)
              .retrieve()
              .body(MAP);
      if (body == null) {
        throw new UnavailableException("eligible unavailable");
      }
      Object routes = body.get("routes");
      if (!(routes instanceof List<?> list)) {
        return List.of();
      }
      List<EligibleRoute> out = new ArrayList<>();
      for (Object item : list) {
        if (item instanceof Map<?, ?> row) {
          out.add(
              new EligibleRoute(
                  string(row.get("route_id")),
                  string(row.get("route_version")),
                  string(row.get("intent_label")),
                  string(row.get("description"))));
        }
      }
      return out;
    } catch (JsonProcessingException e) {
      throw new UnavailableException("eligible unavailable", e);
    } catch (UnavailableException e) {
      throw e;
    } catch (RestClientException e) {
      throw new UnavailableException("eligible unavailable", e);
    }
  }

  private static String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }

  private static Integer integer(Object value) {
    if (value instanceof Number n) {
      return n.intValue();
    }
    return value == null ? null : Integer.valueOf(String.valueOf(value));
  }
}
