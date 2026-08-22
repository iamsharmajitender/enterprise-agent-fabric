package com.fabric.afd.adapters.in.http;

import com.fabric.afd.bootstrap.TraceIds;
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
 * Accept or mint {@code X-Request-Id} at the channel edge. Preserve inbound {@code
 * traceparent} for Micrometer/OTel (do not rewrite). Health stays unauthenticated and still
 * gets a request id for log correlation.
 *
 * <p>Order is after Spring's HTTP observation filter ({@code HIGHEST_PRECEDENCE + 1}) so {@code
 * request_id} lands on the server span. Source: Spring Framework {@code
 * ServerHttpObservationFilter#DEFAULT_ORDER}.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class RequestIdFilter extends OncePerRequestFilter {

  public static final String HEADER_REQUEST_ID = "X-Request-Id";
  public static final String MDC_REQUEST_ID = "request_id";
  public static final String ATTR_REQUEST_ID = "fabric.request_id";

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain chain)
      throws ServletException, IOException {
    String incoming = request.getHeader(HEADER_REQUEST_ID);
    String requestId =
        (incoming == null || incoming.isBlank()) ? "req-" + UUID.randomUUID().toString().replace("-", "").substring(0, 16) : incoming.trim();
    request.setAttribute(ATTR_REQUEST_ID, requestId);
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
