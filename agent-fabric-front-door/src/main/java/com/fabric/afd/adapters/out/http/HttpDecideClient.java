package com.fabric.afd.adapters.out.http;

import com.fabric.afd.application.DecidePort;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.UnavailableException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

public class HttpDecideClient implements DecidePort {

  private static final ParameterizedTypeReference<Map<String, Object>> MAP =
      new ParameterizedTypeReference<>() {};

  private final RestClient http;

  public HttpDecideClient(RestClient http) {
    this.http = http;
  }

  @Override
  public DecideOutcome decide(DecideCall call) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("ingress", call.ingress());
    body.put("channel", call.channel());
    body.put("session_id", call.sessionId());
    if (call.message() != null) {
      body.put("message", call.message());
    }
    body.put("route_id", call.routeId());
    body.put("claims", call.claims() == null ? Map.of() : call.claims());
    try {
      Map<String, Object> response =
          http.post().uri("/v1/intent/decide").body(body).retrieve().body(MAP);
      if (response == null || response.get("outcome") == null) {
        throw new UnavailableException("decide unavailable");
      }
      @SuppressWarnings("unchecked")
      List<Map<String, Object>> candidates =
          response.get("candidates") instanceof List<?> list
              ? (List<Map<String, Object>>) list
              : List.of();
      return new DecideOutcome(
          String.valueOf(response.get("outcome")),
          string(response.get("route_id")),
          string(response.get("route_version")),
          string(response.get("clarify_prompt")),
          candidates);
    } catch (UnavailableException e) {
      throw e;
    } catch (RestClientException e) {
      throw new UnavailableException("decide unavailable", e);
    }
  }

  private static String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }
}
