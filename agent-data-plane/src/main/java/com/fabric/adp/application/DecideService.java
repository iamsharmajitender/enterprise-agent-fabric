package com.fabric.adp.application;

import com.fabric.adp.bootstrap.TraceIds;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.ForbiddenException;
import com.fabric.adp.domain.RouteRow;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class DecideService {

  private final CatalogueService catalogue;
  private final BusinessEvents events;

  public DecideService(CatalogueService catalogue, BusinessEvents events) {
    this.catalogue = catalogue;
    this.events = events;
  }

  public DecideResult decide(DecideRequest request, String workload) {
    if (!"afd".equals(workload)) {
      throw new ForbiddenException("only afd may call decide");
    }
    DecideResult result;
    if ("jobs".equals(request.ingress()) && request.hasRouteId()) {
      result = entitleJob(request);
    } else {
      List<RouteRow> eligible = catalogue.eligible(request.channel(), request.entitledClaims());
      List<String> eligibleIds = eligible.stream().map(RouteRow::routeId).toList();
      if (eligible.isEmpty()) {
        result = DecideResult.abstain(eligibleIds);
      } else if (request.hasRouteId()) {
        result =
            eligible.stream()
                .filter(row -> row.routeId().equals(request.routeId()))
                .findFirst()
                .map(row -> DecideResult.route(row, 1.0, eligibleIds))
                .orElseGet(() -> DecideResult.abstain(eligibleIds));
      } else {
        result = keywordRetrieve(request.message(), eligible, eligibleIds);
      }
    }
    emitDecide(request, result);
    TraceIds.put("session_id", request.sessionId());
    TraceIds.put("outcome", result.outcome());
    TraceIds.put("route_id", result.routeId());
    TraceIds.put("route_version", result.routeVersion());
    return result;
  }

  private void emitDecide(DecideRequest request, DecideResult result) {
    String prefix = "jobs".equals(request.ingress()) ? "job" : "chat";
    String journeyId =
        result.routeId() != null ? prefix + "." + result.routeId() : prefix + ".decide";
    String event =
        switch (result.outcome()) {
          case "route" -> "intent.decide.routed";
          case "clarify" -> "intent.decide.clarify";
          default -> "intent.decide.abstain";
        };
    events.emit(
        event,
        journeyId,
        BusinessEvents.fields(
            "outcome",
            result.outcome(),
            "route_id",
            result.routeId(),
            "route_version",
            result.routeVersion(),
            "session_id",
            request.sessionId(),
            "channel",
            request.channel(),
            "ingress",
            request.ingress(),
            "eligible_count",
            String.valueOf(result.eligibleRoutes() == null ? 0 : result.eligibleRoutes().size())));
    events.countDecide(journeyId, result.outcome(), request.channel());
  }

  private DecideResult entitleJob(DecideRequest request) {
    List<RouteRow> entitled =
        catalogue.list().stream()
            .filter(row -> request.entitledClaims().containsAll(row.requiredClaims()))
            .toList();
    List<String> entitledIds = entitled.stream().map(RouteRow::routeId).toList();
    return entitled.stream()
        .filter(row -> row.routeId().equals(request.routeId()))
        .findFirst()
        .map(row -> DecideResult.route(row, 1.0, entitledIds))
        .orElseGet(() -> DecideResult.abstain(entitledIds));
  }

  private DecideResult keywordRetrieve(
      String message, List<RouteRow> eligible, List<String> eligibleIds) {
    String haystack = message == null ? "" : message.toLowerCase(Locale.ROOT);
    record Scored(RouteRow row, int score) {}
    List<Scored> scored = new ArrayList<>();
    for (RouteRow row : eligible) {
      int score = 0;
      for (String keyword : row.keywords()) {
        if (haystack.contains(keyword.toLowerCase(Locale.ROOT))) {
          score++;
        }
      }
      scored.add(new Scored(row, score));
    }
    scored.sort(Comparator.comparingInt(Scored::score).reversed());
    int best = scored.getFirst().score();
    if (best <= 0) {
      return DecideResult.abstain(eligibleIds);
    }
    List<Scored> top = scored.stream().filter(s -> s.score() == best).toList();
    if (top.size() == 1) {
      return DecideResult.route(top.getFirst().row(), 0.91, eligibleIds);
    }
    List<Map<String, Object>> candidates = new ArrayList<>();
    for (Scored hit : top.stream().limit(2).toList()) {
      Map<String, Object> c = new LinkedHashMap<>();
      c.put("intent_label", hit.row().intentLabel());
      c.put("route_id", hit.row().routeId());
      c.put("confidence", 0.6);
      c.put("label", hit.row().description());
      candidates.add(c);
    }
    return DecideResult.clarify(
        "Did you want a fee explanation or recent transactions?", candidates, eligibleIds);
  }
}
