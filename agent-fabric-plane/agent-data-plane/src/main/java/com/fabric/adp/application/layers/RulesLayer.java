package com.fabric.adp.application.layers;

import com.fabric.adp.application.IntentRuleStore;
import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.IntentRule;
import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

/**
 * Layer ① — rules. First match wins. Only a {@code route_id} already in {@code eligible} may bind.
 *
 * <p>Named {@code route_id} (jobs body or chat chip) always binds or abstains here — never ②/③.
 * Chat commands ({@code /hr}) come from {@link IntentRuleStore}, not hardcoded utterances. Jobs do
 * not parse slash from the body.
 */
public class RulesLayer implements DecideLayer {

  static final double BIND_CONFIDENCE = 1.0;
  static final String KIND_COMMAND = "command";

  private final IntentRuleStore rules;

  public RulesLayer(IntentRuleStore rules) {
    this.rules = rules;
  }

  @Override
  public Optional<DecideResult> apply(DecideRequest request, List<RouteRow> eligible) {
    if (request.hasRouteId()) {
      return Optional.of(bindOrAbstain(eligible, request.routeId()));
    }
    if ("jobs".equals(request.ingress())) {
      return Optional.empty();
    }
    String needle = normalize(request.message());
    if (needle.isEmpty()) {
      return Optional.empty();
    }
    for (IntentRule rule : rules.list()) {
      if (!KIND_COMMAND.equals(rule.matchKind())) {
        continue;
      }
      if (!needle.equals(normalize(rule.matchValue()))) {
        continue;
      }
      return Optional.of(bindOrAbstain(eligible, rule.routeId()));
    }
    return Optional.empty();
  }

  private static DecideResult bindOrAbstain(List<RouteRow> rows, String routeId) {
    List<String> ids = LayerIds.of(rows);
    for (RouteRow row : rows) {
      if (row.routeId().equals(routeId)) {
        return DecideResult.route(row, BIND_CONFIDENCE, ids);
      }
    }
    return DecideResult.abstain(ids);
  }

  private static String normalize(String value) {
    return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
  }
}
