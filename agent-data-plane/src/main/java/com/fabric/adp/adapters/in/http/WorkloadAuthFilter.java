package com.fabric.adp.adapters.in.http;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Set;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class WorkloadAuthFilter extends OncePerRequestFilter {

  public static final String ATTR_WORKLOAD = "fabric.workload";
  private static final Set<String> WORKLOADS = Set.of("afd", "adp", "acp", "ar", "acr");

  @Override
  protected boolean shouldNotFilter(HttpServletRequest request) {
    return "/health".equals(request.getRequestURI());
  }

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain chain)
      throws ServletException, IOException {
    String authorization = request.getHeader(HttpHeaders.AUTHORIZATION);
    String workload = request.getHeader("X-Workload");
    if (!"Bearer fabric-internal".equals(authorization)
        || workload == null
        || !WORKLOADS.contains(workload)) {
      response.sendError(HttpServletResponse.SC_UNAUTHORIZED);
      return;
    }
    request.setAttribute(ATTR_WORKLOAD, workload);
    chain.doFilter(request, response);
  }
}
