package com.fabric.afd.adapters.out.http;

import com.fabric.afd.adapters.in.http.RequestIdFilter;
import java.io.IOException;
import org.slf4j.MDC;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;

/** Forward the edge {@code X-Request-Id} on RestClient calls to ADP and AR. */
public final class RequestIdInterceptor implements ClientHttpRequestInterceptor {

  @Override
  public ClientHttpResponse intercept(
      HttpRequest request, byte[] body, ClientHttpRequestExecution execution) throws IOException {
    String requestId = MDC.get(RequestIdFilter.MDC_REQUEST_ID);
    if (requestId != null
        && !requestId.isBlank()
        && request.getHeaders().getFirst(RequestIdFilter.HEADER_REQUEST_ID) == null) {
      request.getHeaders().set(RequestIdFilter.HEADER_REQUEST_ID, requestId);
    }
    return execution.execute(request, body);
  }
}
