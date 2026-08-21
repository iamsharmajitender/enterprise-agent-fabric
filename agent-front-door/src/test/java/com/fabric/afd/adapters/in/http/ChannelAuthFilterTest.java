package com.fabric.afd.adapters.in.http;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

class ChannelAuthFilterTest {

  private final ChannelAuthFilter filter = new ChannelAuthFilter(new ObjectMapper());

  @Test
  void healthAndScratchpadsSkipChannelAuth() throws Exception {
    assertThat(filter.shouldNotFilter(request("/health"))).isTrue();
    assertThat(filter.shouldNotFilter(request("/chat.html"))).isTrue();
    assertThat(filter.shouldNotFilter(request("/jobs.html"))).isTrue();
  }

  @Test
  void jobsStillRequireChannelAuth() throws Exception {
    assertThat(filter.shouldNotFilter(request("/v1/jobs"))).isFalse();
  }

  private static MockHttpServletRequest request(String path) {
    MockHttpServletRequest request = new MockHttpServletRequest("GET", path);
    request.setRequestURI(path);
    return request;
  }
}
