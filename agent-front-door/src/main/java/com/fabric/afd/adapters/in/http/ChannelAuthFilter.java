package com.fabric.afd.adapters.in.http;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Map;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class ChannelAuthFilter extends OncePerRequestFilter {

  public static final String ATTR_CLAIMS = "fabric.claims";

  private final ObjectMapper mapper;

  public ChannelAuthFilter(ObjectMapper mapper) {
    this.mapper = mapper;
  }

  @Override
  protected boolean shouldNotFilter(HttpServletRequest request) {
    String path = request.getRequestURI();
    return "/health".equals(path) || "/chat.html".equals(path) || "/jobs.html".equals(path);
  }

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain chain)
      throws ServletException, IOException {
    String authorization = request.getHeader(HttpHeaders.AUTHORIZATION);
    String claimsHeader = request.getHeader("X-Stub-Claims");
    if (!"Bearer stub".equals(authorization) || claimsHeader == null || claimsHeader.isBlank()) {
      response.sendError(HttpServletResponse.SC_UNAUTHORIZED);
      return;
    }
    try {
      Map<String, Object> claims = mapper.readValue(claimsHeader, new TypeReference<>() {});
      request.setAttribute(ATTR_CLAIMS, claims);
    } catch (Exception e) {
      response.sendError(HttpServletResponse.SC_UNAUTHORIZED);
      return;
    }
    chain.doFilter(request, response);
  }
}
