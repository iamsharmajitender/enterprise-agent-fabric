package com.fabric.afd.application;

import com.fabric.afd.bootstrap.TraceIds;
import com.fabric.afd.domain.BadRequestException;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.ForbiddenException;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.RunStart;
import com.fabric.afd.domain.SessionIds;
import java.util.Map;

public class JobsService {

  private final DecidePort decide;
  private final CataloguePort catalogue;
  private final RuntimePort runtime;
  private final FreezeStore freeze;
  private final BusinessEvents events;
  private final AuditPort audit;

  public JobsService(
      DecidePort decide,
      CataloguePort catalogue,
      RuntimePort runtime,
      FreezeStore freeze,
      BusinessEvents events) {
    this(decide, catalogue, runtime, freeze, events, AuditPort.NOOP);
  }

  public JobsService(
      DecidePort decide,
      CataloguePort catalogue,
      RuntimePort runtime,
      FreezeStore freeze,
      BusinessEvents events,
      AuditPort audit) {
    this.decide = decide;
    this.catalogue = catalogue;
    this.runtime = runtime;
    this.freeze = freeze;
    this.events = events;
    this.audit = audit == null ? AuditPort.NOOP : audit;
  }

  public String start(
      String routeId, String idempotencyKey, Map<String, Object> payload, Map<String, Object> claims) {
    if (blank(routeId) || blank(idempotencyKey)) {
      throw new BadRequestException("route_id and idempotency_key are required");
    }
    String sessionId = SessionIds.mintJobOrSub(idempotencyKey);
    String journeyId = "job." + routeId;
    TraceIds.put("session_id", sessionId);
    TraceIds.put("route_id", routeId);
    TraceIds.put("journey_id", journeyId);
    events.emit(
        "job.entitlement.accepted",
        journeyId,
        BusinessEvents.fields(
            "session_id",
            sessionId,
            "route_id",
            routeId,
            "channel",
            "web",
            "ingress",
            "jobs",
            "outcome",
            "accepted"));
    DecideOutcome outcome =
        decide.decide(new DecideCall("jobs", "web", sessionId, null, routeId, claims));
    TraceIds.put("outcome", outcome.outcome());
    if (!outcome.routed()) {
      events.emit(
          "job.entitlement.rejected",
          journeyId,
          BusinessEvents.fields(
              "session_id",
              sessionId,
              "route_id",
              routeId,
              "channel",
              "web",
              "ingress",
              "jobs",
              "outcome",
              outcome.outcome()));
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
    audit.emitAsync(
        AuditEvents.freezeWritten(
            correlationId,
            sessionId,
            row.routeId(),
            row.routeVersion(),
            "jobs",
            SessionIds.parentCorrelationId(idempotencyKey)));
    events.emit(
        "job.run.started",
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
            "jobs",
            "outcome",
            "started"));
    events.countOutcome(journeyId, "started", "web");
    return correlationId;
  }

  public Map<String, Object> status(String correlationId) {
    TraceIds.put("correlation_id", correlationId);
    FrozenRoute live = freeze.findByCorrelationId(correlationId);
    if (live != null) {
      TraceIds.put("session_id", live.sessionId());
      TraceIds.put("route_id", live.routeId());
    }
    Map<String, Object> body =
        runtime.status(
            correlationId, live == null ? null : live.activationTarget());
    if (live != null && "completed".equals(String.valueOf(body.get("status")))) {
      String journeyId =
          live.routeId() == null ? "job.turn" : "job." + live.routeId();
      events.emit(
          "job.run.delivered",
          journeyId,
          BusinessEvents.fields(
              "session_id",
              live.sessionId(),
              "correlation_id",
              correlationId,
              "route_id",
              live.routeId(),
              "route_version",
              live.routeVersion(),
              "channel",
              "web",
              "ingress",
              "jobs",
              "outcome",
              "delivered",
              "status",
              "completed"));
      events.countOutcome(journeyId, "completed", "web");
    }
    return body;
  }

  private static boolean blank(String value) {
    return value == null || value.isBlank();
  }
}
