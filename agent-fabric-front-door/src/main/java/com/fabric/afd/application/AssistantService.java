package com.fabric.afd.application;

import com.fabric.afd.bootstrap.TraceIds;
import com.fabric.afd.domain.BadRequestException;
import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;
import com.fabric.afd.domain.EligibleRoute;
import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.NotFoundException;
import com.fabric.afd.domain.RunStart;
import com.fabric.afd.domain.SessionIds;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

public class AssistantService {

  private static final String CHANNEL = "web";
  private static final String INGRESS = "chat";

  private final DecidePort decide;
  private final CataloguePort catalogue;
  private final RuntimePort runtime;
  private final FreezeStore freeze;
  private final BusinessEvents events;
  private final AuditPort audit;

  public AssistantService(
      DecidePort decide,
      CataloguePort catalogue,
      RuntimePort runtime,
      FreezeStore freeze,
      BusinessEvents events) {
    this(decide, catalogue, runtime, freeze, events, AuditPort.NOOP);
  }

  public AssistantService(
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

  public Map<String, Object> hints(String sessionId, Map<String, Object> claims) {
    String sid = orMint(sessionId);
    TraceIds.put("session_id", sid);
    List<Map<String, Object>> hints = new ArrayList<>();
    for (EligibleRoute route : catalogue.eligible(CHANNEL, claims)) {
      String hintId = "hint-" + token(8);
      freeze.putOpaque(sid, hintId, route.routeId());
      Map<String, Object> chip = new LinkedHashMap<>();
      chip.put("hint_id", hintId);
      chip.put("label", label(route));
      hints.add(chip);
    }
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("session_id", sid);
    body.put("hints", hints);
    return body;
  }

  public Map<String, Object> turn(
      String sessionId, String message, String hintId, String optionId, Map<String, Object> claims) {
    String sid = orMint(sessionId);
    TraceIds.put("session_id", sid);
    events.emit(
        "chat.turn.received",
        "chat.turn",
        BusinessEvents.fields(
            "session_id",
            sid,
            "channel",
            CHANNEL,
            "ingress",
            INGRESS,
            "has_hint",
            String.valueOf(!blank(hintId)),
            "has_option",
            String.valueOf(!blank(optionId))));
    if (blank(message) && blank(hintId) && blank(optionId)) {
      throw new BadRequestException("message, hint_id, or option_id is required");
    }
    if (blank(hintId) && blank(optionId)) {
      FrozenRoute live = freeze.get(sid);
      if (live != null && live.correlationId() != null && isWaiting(live.correlationId())) {
        return resume(live, message);
      }
      Optional<FrozenRoute> open = runtime.openRun(sid);
      if (open.isPresent()
          && open.get().correlationId() != null
          && isWaiting(open.get().correlationId())) {
        freeze.save(open.get());
        return resume(open.get(), message);
      }
    }
    String routeId = resolve(sid, hintId, optionId);
    DecideOutcome outcome =
        decide.decide(new DecideCall(INGRESS, CHANNEL, sid, message, routeId, claims));
    TraceIds.put("outcome", outcome.outcome());
    TraceIds.put("route_id", outcome.routeId());
    if ("clarify".equals(outcome.outcome())) {
      return clarify(sid, outcome);
    }
    if (!outcome.routed()) {
      Map<String, Object> body = new LinkedHashMap<>();
      body.put("session_id", sid);
      body.put("status", "abstain");
      return body;
    }
    CatalogRoute row = catalogue.get(outcome.routeId(), outcome.routeVersion());
    String key = sid + ":" + row.routeId() + ":v1";
    String journeyId = "chat." + row.routeId();
    String correlationId =
        runtime.start(
            new RunStart(key, sid, row, Map.of("utterance", message == null ? "" : message)));
    TraceIds.put("correlation_id", correlationId);
    TraceIds.put("route_id", row.routeId());
    TraceIds.put("route_version", row.routeVersion());
    TraceIds.put("journey_id", journeyId);
    freeze.save(
        new FrozenRoute(
            sid,
            key,
            row.routeId(),
            row.routeVersion(),
            row.activationTarget(),
            row.agentClientId(),
            correlationId));
    audit.emitAsync(
        AuditEvents.freezeWritten(
            correlationId, sid, row.routeId(), row.routeVersion(), INGRESS));
    events.emit(
        "chat.run.started",
        journeyId,
        BusinessEvents.fields(
            "session_id",
            sid,
            "correlation_id",
            correlationId,
            "route_id",
            row.routeId(),
            "route_version",
            row.routeVersion(),
            "channel",
            CHANNEL,
            "ingress",
            INGRESS,
            "outcome",
            "started"));
    events.countOutcome(journeyId, "started", CHANNEL);
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("session_id", sid);
    body.put("status", "accepted");
    return body;
  }

  public Map<String, Object> events(String sessionId) {
    FrozenRoute live = freeze.get(sessionId);
    if (live == null || live.correlationId() == null) {
      live = runtime.openRun(sessionId).orElse(null);
      if (live != null) {
        freeze.save(live);
      }
    }
    if (live == null || live.correlationId() == null) {
      throw new NotFoundException(sessionId);
    }
    TraceIds.put("session_id", sessionId);
    TraceIds.put("correlation_id", live.correlationId());
    TraceIds.put("route_id", live.routeId());
    Map<String, Object> status = runtime.status(live.correlationId());
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("session_id", sessionId);
    body.put("status", status.get("status"));
    Object result = status.get("result");
    if (result instanceof Map<?, ?> map && map.get("message") != null) {
      body.put("message", map.get("message"));
    }
    String journeyId = live.routeId() == null ? "chat.turn" : "chat." + live.routeId();
    if ("completed".equals(String.valueOf(status.get("status")))) {
      events.emit(
          "chat.run.delivered",
          journeyId,
          BusinessEvents.fields(
              "session_id",
              sessionId,
              "correlation_id",
              live.correlationId(),
              "route_id",
              live.routeId(),
              "channel",
              CHANNEL,
              "ingress",
              INGRESS,
              "outcome",
              "delivered",
              "status",
              "completed"));
      events.countOutcome(journeyId, "completed", CHANNEL);
    }
    return body;
  }

  private Map<String, Object> resume(FrozenRoute live, String message) {
    TraceIds.put("session_id", live.sessionId());
    TraceIds.put("correlation_id", live.correlationId());
    TraceIds.put("route_id", live.routeId());
    runtime.resume(live.correlationId(), message);
    freeze.save(live);
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("session_id", live.sessionId());
    body.put("status", "accepted");
    return body;
  }

  private boolean isWaiting(String correlationId) {
    return "waiting".equals(String.valueOf(runtime.status(correlationId).get("status")));
  }

  private Map<String, Object> clarify(String sid, DecideOutcome outcome) {
    List<Map<String, Object>> options = new ArrayList<>();
    for (Map<String, Object> candidate : outcome.candidates()) {
      String routeId = string(candidate.get("route_id"));
      if (blank(routeId)) {
        continue;
      }
      String optionId = "opt-" + token(8);
      freeze.putOpaque(sid, optionId, routeId);
      Map<String, Object> option = new LinkedHashMap<>();
      option.put("id", optionId);
      option.put("label", string(candidate.get("label")));
      options.add(option);
    }
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("session_id", sid);
    body.put("status", "clarify");
    body.put("prompt", outcome.clarifyPrompt());
    body.put("options", options);
    return body;
  }

  private String resolve(String sessionId, String hintId, String optionId) {
    if (!blank(hintId)) {
      return freeze.resolveOpaque(sessionId, hintId);
    }
    if (!blank(optionId)) {
      return freeze.resolveOpaque(sessionId, optionId);
    }
    return null;
  }

  private static String label(EligibleRoute route) {
    return !blank(route.description()) ? route.description() : route.intentLabel();
  }

  private static String orMint(String sessionId) {
    if (blank(sessionId)) {
      return SessionIds.mintChat();
    }
    String sid = sessionId.trim();
    if (sid.startsWith("job-")
        || sid.startsWith("sub-")
        || sid.startsWith("job:")
        || sid.startsWith("subagent-")) {
      throw new BadRequestException("session_id must be a chat session (chat-{uuid})");
    }
    if (!SessionIds.isChatSession(sid)) {
      throw new BadRequestException("session_id must be chat-{uuid}");
    }
    return sid;
  }

  private static String token(int n) {
    return UUID.randomUUID().toString().replace("-", "").substring(0, n);
  }

  private static boolean blank(String value) {
    return value == null || value.isBlank();
  }

  private static String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }
}
