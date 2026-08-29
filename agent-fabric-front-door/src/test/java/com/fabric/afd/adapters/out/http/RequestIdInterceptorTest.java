package com.fabric.afd.adapters.out.http;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.afd.adapters.in.http.RequestIdFilter;
import java.io.IOException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.mock.http.client.MockClientHttpRequest;
import org.springframework.mock.http.client.MockClientHttpResponse;

class RequestIdInterceptorTest {

  private final RequestIdInterceptor interceptor = new RequestIdInterceptor();

  @AfterEach
  void clearMdc() {
    MDC.clear();
  }

  @Test
  void forwardsMdcRequestIdWhenHeaderMissing() throws IOException {
    MDC.put(RequestIdFilter.MDC_REQUEST_ID, "req-from-edge");
    MockClientHttpRequest request = new MockClientHttpRequest();
    ClientHttpRequestExecution execution =
        (req, body) -> {
          assertThat(req.getHeaders().getFirst(RequestIdFilter.HEADER_REQUEST_ID))
              .isEqualTo("req-from-edge");
          return new MockClientHttpResponse(new byte[0], 200);
        };

    interceptor.intercept(request, new byte[0], execution);
  }

  @Test
  void doesNotOverwriteExistingHeader() throws IOException {
    MDC.put(RequestIdFilter.MDC_REQUEST_ID, "req-from-edge");
    MockClientHttpRequest request = new MockClientHttpRequest();
    request.getHeaders().set(RequestIdFilter.HEADER_REQUEST_ID, "req-already-set");
    ClientHttpRequestExecution execution =
        (req, body) -> {
          assertThat(req.getHeaders().getFirst(RequestIdFilter.HEADER_REQUEST_ID))
              .isEqualTo("req-already-set");
          return new MockClientHttpResponse(new byte[0], 200);
        };

    interceptor.intercept(request, new byte[0], execution);
  }

  @Test
  void skipsWhenMdcEmpty() throws IOException {
    MockClientHttpRequest request = new MockClientHttpRequest();
    ClientHttpRequestExecution execution =
        (HttpRequest req, byte[] body) -> {
          assertThat(req.getHeaders().getFirst(RequestIdFilter.HEADER_REQUEST_ID)).isNull();
          return new MockClientHttpResponse(new byte[0], 200);
        };

    interceptor.intercept(request, new byte[0], execution);
  }
}
