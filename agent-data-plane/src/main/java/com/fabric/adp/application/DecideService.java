package com.fabric.adp.application;

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

  public DecideService(CatalogueService catalogue) {
    this.catalogue = catalogue;
  }

  public DecideResult decide(DecideRequest request, String workload) {
    if (!"afd".equals(workload)) {
      throw new ForbiddenException("only afd may call decide");
    }
    List<RouteRow> eligible = catalogue.eligible(request.channel(), request.entitledClaims());
    List<String> eligibleIds = eligible.stream().map(RouteRow::routeId).toList();
    if (eligible.isEmpty()) {
      return DecideResult.abstain(eligibleIds);
    }
    if (request.hasRouteId()) {
      return eligible.stream()
          .filter(row -> row.routeId().equals(request.routeId()))
          .findFirst()
          .map(row -> DecideResult.route(row, 1.0, eligibleIds))
          .orElseGet(() -> DecideResult.abstain(eligibleIds));
    }
    return keywordRetrieve(request.message(), eligible, eligibleIds);
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
