package com.fabric.registry.adapters.out.http;

import com.fabric.registry.application.AuditPort;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.client.RestClient;

public class HttpAuditClient implements AuditPort {

  private static final Logger log = LoggerFactory.getLogger(HttpAuditClient.class);
  private final RestClient client;
  private final boolean enabled;
  private final ExecutorService pool;

  public HttpAuditClient(RestClient client, boolean enabled) {
    this.client = client;
    this.enabled = enabled;
    this.pool =
        Executors.newSingleThreadExecutor(
            r -> {
              Thread t = new Thread(r, "acr-audit-emit");
              t.setDaemon(true);
              return t;
            });
  }

  @Override
  public void emitAsync(Map<String, Object> event) {
    if (!enabled || event == null) {
      return;
    }
    pool.execute(
        () -> {
          try {
            client.post().uri("/v1/audit/events").body(event).retrieve().toBodilessEntity();
          } catch (Exception ex) {
            log.warn("audit emit failed type={}", event.get("event_type"), ex);
          }
        });
  }
}
