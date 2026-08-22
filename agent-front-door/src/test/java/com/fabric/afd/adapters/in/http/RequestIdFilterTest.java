package com.fabric.afd.adapters.in.http;

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
  void mintsRequestIdWhenMissing() throws Exception {
    MockHttpServletRequest request = new MockHttpServletRequest("GET", "/health");
    MockHttpServletResponse response = new MockHttpServletResponse();
    FilterChain chain =
        (req, res) -> assertThat(MDC.get(RequestIdFilter.MDC_REQUEST_ID)).startsWith("req-");

    filter.doFilter(request, response, chain);

    String id = response.getHeader(RequestIdFilter.HEADER_REQUEST_ID);
    assertThat(id).isNotBlank().startsWith("req-");
    assertThat(request.getAttribute(RequestIdFilter.ATTR_REQUEST_ID)).isEqualTo(id);
  }

  @Test
  void echoesProvidedRequestId() throws Exception {
    MockHttpServletRequest request = new MockHttpServletRequest("POST", "/v1/jobs");
    request.addHeader(RequestIdFilter.HEADER_REQUEST_ID, "req-fixed-id-001");
    MockHttpServletResponse response = new MockHttpServletResponse();
    FilterChain chain = (req, res) -> {};

    filter.doFilter(request, response, chain);

    assertThat(response.getHeader(RequestIdFilter.HEADER_REQUEST_ID)).isEqualTo("req-fixed-id-001");
  }
}
