package com.fabric.adp.adapters.in.http;

import static org.assertj.core.api.Assertions.assertThat;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

class RequestIdFilterTest {

  private final RequestIdFilter filter = new RequestIdFilter();

  @AfterEach
  void clearMdc() {
    MDC.clear();
  }

  @Test
  void echoesProvidedRequestId() throws Exception {
    MockHttpServletRequest request = new MockHttpServletRequest("POST", "/v1/intent/decide");
    request.addHeader(RequestIdFilter.HEADER_REQUEST_ID, "req-from-afd");
    MockHttpServletResponse response = new MockHttpServletResponse();
    FilterChain chain =
        (req, res) -> assertThat(MDC.get(RequestIdFilter.MDC_REQUEST_ID)).isEqualTo("req-from-afd");

    filter.doFilter(request, response, chain);

    assertThat(response.getHeader(RequestIdFilter.HEADER_REQUEST_ID)).isEqualTo("req-from-afd");
  }
}
