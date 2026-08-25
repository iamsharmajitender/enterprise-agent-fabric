package com.fabric.afd.application;

import com.fabric.afd.bootstrap.TraceIds;
import com.fabric.afd.domain.BadRequestException;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.ForbiddenException;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.RunStart;
import java.util.Map;

public class JobsService {

  private final DecidePort decide;
  private final CataloguePort catalogue;
  private final RuntimePort runtime;
  private final FreezeStore freeze;
  private final BusinessEvents events;

  public JobsService(
      DecidePort decide,
      CataloguePort catalogue,
      RuntimePort runtime,
      FreezeStore freeze,
      BusinessEvents events) {
    this.decide = decide;
    this.catalogue = catalogue;
    this.runtime = runtime;
    this.freeze = freeze;
    this.events = events;
  }

  public String start(
      String routeId, String idempotencyKey, Map<String, Object> payload, Map<String, Object> claims) {
    if (blank(routeId) || blank(idempotencyKey)) {
      throw new BadRequestException("route_id and idempotency_key are required");
    }
    String sessionId = "job:" + idempotencyKey;
    String journeyId = "job." + routeId;
    TraceIds.put("session_id", sessionId);
    TraceIds.put("route_id", routeId);
    TraceIds.put("journey_id", journeyId);
    events.emit(
        "job.entitle.accepted",
        journeyId,
        BusinessEvents.fields(
            "session_id",
            sessionId,
            "route_id",
            routeId,
            "channel",
            "web",
            "ingress",
            "jobs"));
    DecideOutcome outcome =
        decide.decide(new DecideCall("jobs", "web", sessionId, null, routeId, claims));
    TraceIds.put("outcome", outcome.outcome());
    if (!outcome.routed()) {
      events.emit(
          "job.entitle.rejected",
          journeyId,
          BusinessEvents.fields("route_id", routeId, "outcome", outcome.outcome()));
      events.countOutcome(journeyId, "rejected", "web");
      throw new ForbiddenException("not entitled for route");
    }
    CatalogRoute row = catalogue.get(outcome.routeId(), outcome.routeVersion());
    String correlationId =
        runtime.start(new RunStart(idempotencyKey, sessionId, row, payload == null ? Map.of() : payload));
    TraceIds.put("correlation_id", correlationId);
    TraceIds.put("route_version", row.routeVersion());
    freeze.save(
        new FrozenRoute(
            sessionId,
            idempotencyKey,
            row.routeId(),
            row.routeVersion(),
            row.activationTarget(),
            row.agentClientId(),
            correlationId));
    events.emit(
        "job.run.accepted",
        journeyId,
        BusinessEvents.fields(
            "session_id",
            sessionId,
            "correlation_id",
            correlationId,
            "route_id",
            row.routeId(),
            "route_version",
            row.routeVersion(),
            "channel",
            "web",
            "ingress",
            "jobs"));
    events.countOutcome(journeyId, "accepted", "web");
    return correlationId;
  }

  public Map<String, Object> status(String correlationId) {
    TraceIds.put("correlation_id", correlationId);
    return runtime.status(correlationId);
  }

  private static boolean blank(String value) {
    return value == null || value.isBlank();
  }
}
