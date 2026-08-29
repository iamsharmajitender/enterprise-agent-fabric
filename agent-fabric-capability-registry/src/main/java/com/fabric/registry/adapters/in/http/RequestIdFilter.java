package com.fabric.registry.adapters.in.http;

import com.fabric.registry.bootstrap.TraceIds;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Accept or mint {@code X-Request-Id}. After the HTTP observation filter so the id is on the
 * server span.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class RequestIdFilter extends OncePerRequestFilter {

  public static final String HEADER_REQUEST_ID = "X-Request-Id";
  public static final String MDC_REQUEST_ID = "request_id";

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain chain)
      throws ServletException, IOException {
    String incoming = request.getHeader(HEADER_REQUEST_ID);
    String requestId =
        (incoming == null || incoming.isBlank())
            ? "req-" + UUID.randomUUID()
            : incoming.trim();
    response.setHeader(HEADER_REQUEST_ID, requestId);
    MDC.put(MDC_REQUEST_ID, requestId);
    TraceIds.put(MDC_REQUEST_ID, requestId);
    try {
      chain.doFilter(request, response);
    } finally {
      MDC.remove(MDC_REQUEST_ID);
    }
  }
}
