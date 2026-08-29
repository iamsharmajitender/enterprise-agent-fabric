package com.fabric.adp.application.layers;

import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.RouteRow;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Layer ② — classifier. Runs only over {@code eligible}. Unique retrieve winner at or above the
 * row's {@link com.fabric.adp.domain.RiskClass#routeBar()} → route; unique below the bar or a close
 * top-2 → clarify; OOD / no neighbor → empty (so ③ can try, only if ② finished under budget).
 *
 * <p>In-process kNN over labelled seed utterances ({@link RetrieveIndex}). Do not score
 * {@code RouteRow.keywords}.
 */
public class ClassifierLayer implements DecideLayer {

  static final double RETRIEVE_CONFIDENCE = 0.91;
  static final double TIE_CONFIDENCE = 0.6;

  private static final String CLARIFY_PROMPT =
      "Did you want a fee explanation or recent transactions?";

  private final RetrieveIndex index;

  public ClassifierLayer() {
    this(RetrieveIndex.loadDefault());
  }

  ClassifierLayer(RetrieveIndex index) {
    this.index = index;
  }

  @Override
  public Optional<DecideResult> apply(DecideRequest request, List<RouteRow> eligible) {
    if (eligible.isEmpty()) {
      return Optional.empty();
    }
    return retrieve(request.message(), eligible);
  }

  private Optional<DecideResult> retrieve(String message, List<RouteRow> eligible) {
    record Scored(RouteRow row, double score) {}

    List<Scored> scored = new ArrayList<>();
    for (RouteRow row : eligible) {
      double score = index.bestScore(message, row.routeId());
      if (score >= RetrieveIndex.OOD_THRESHOLD) {
        scored.add(new Scored(row, score));
      }
    }
    List<String> ids = LayerIds.of(eligible);
    if (scored.isEmpty()) {
      return Optional.empty();
    }
    scored.sort(Comparator.comparingDouble(Scored::score).reversed());
    Scored best = scored.getFirst();
    boolean unique =
        scored.size() == 1
            || best.score() - scored.get(1).score() >= RetrieveIndex.TIE_MARGIN;
    if (unique) {
      return uniqueWinner(best.row(), ids);
    }

    List<Map<String, Object>> candidates = new ArrayList<>();
    for (Scored hit : scored.subList(0, Math.min(2, scored.size()))) {
      candidates.add(candidate(hit.row(), TIE_CONFIDENCE));
    }
    return Optional.of(DecideResult.clarify(CLARIFY_PROMPT, candidates, ids));
  }

  private static Optional<DecideResult> uniqueWinner(RouteRow winner, List<String> ids) {
    if (RETRIEVE_CONFIDENCE < winner.riskClass().routeBar()) {
      return Optional.of(
          DecideResult.clarify(
              "This is a high-risk action. Did you mean " + winner.intentLabel() + "?",
              List.of(candidate(winner, RETRIEVE_CONFIDENCE)),
              ids));
    }
    return Optional.of(DecideResult.route(winner, RETRIEVE_CONFIDENCE, ids));
  }

  private static Map<String, Object> candidate(RouteRow row, double confidence) {
    Map<String, Object> candidate = new LinkedHashMap<>();
    candidate.put("intent_label", row.intentLabel());
    candidate.put("route_id", row.routeId());
    candidate.put("confidence", confidence);
    candidate.put("label", row.description());
    return candidate;
  }
}
