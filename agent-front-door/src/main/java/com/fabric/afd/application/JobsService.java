package com.fabric.afd.application;

import com.fabric.afd.domain.BadRequestException;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.ForbiddenException;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.RunStart;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class JobsService {

  private static final Logger log = LoggerFactory.getLogger(JobsService.class);

  private final DecidePort decide;
  private final CataloguePort catalogue;
  private final RuntimePort runtime;
  private final FreezeStore freeze;

  public JobsService(
      DecidePort decide, CataloguePort catalogue, RuntimePort runtime, FreezeStore freeze) {
    this.decide = decide;
    this.catalogue = catalogue;
    this.runtime = runtime;
    this.freeze = freeze;
  }

  public String start(String routeId, String idempotencyKey, Map<String, Object> payload, Map<String, Object> claims) {
    if (blank(routeId) || blank(idempotencyKey)) {
      throw new BadRequestException("route_id and idempotency_key are required");
    }
    String sessionId = "job:" + idempotencyKey;
    DecideOutcome outcome =
        decide.decide(new DecideCall("jobs", "web", sessionId, null, routeId, claims));
    if (!outcome.routed()) {
      log.info("job_rejected route_id={} outcome={}", routeId, outcome.outcome());
      throw new ForbiddenException("not entitled for route");
    }
    CatalogRoute row = catalogue.get(outcome.routeId(), outcome.routeVersion());
    String correlationId =
        runtime.start(new RunStart(idempotencyKey, sessionId, row, payload == null ? Map.of() : payload));
    freeze.save(
        new FrozenRoute(
            sessionId,
            idempotencyKey,
            row.routeId(),
            row.routeVersion(),
            row.activationTarget(),
            row.agentClientId(),
            correlationId));
    log.info("job_accepted route_id={} correlation_id={}", row.routeId(), correlationId);
    return correlationId;
  }

  public Map<String, Object> status(String correlationId) {
    return runtime.status(correlationId);
  }

  private static boolean blank(String value) {
    return value == null || value.isBlank();
  }
}
