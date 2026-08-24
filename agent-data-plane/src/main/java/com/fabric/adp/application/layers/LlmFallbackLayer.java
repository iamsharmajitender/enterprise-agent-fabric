package com.fabric.adp.application.layers;

import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.RouteRow;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * Layer ③ — LLM fallback. Rare. Default <b>off</b>. Not a catalogue route and not a Runtime run:
 * ADP would HTTP a model gateway with the utterance plus the eligible {@code route_id} list, then
 * bind the JSON here.
 *
 * <p>{@link #apply} is a no-op while disabled. Jobs / named {@code route_id} never reach this layer
 * (① already returned). Bounded pool + timeout live in {@link LlmFallbackPool}. I12 turns the flag
 * on for ② maybe / high-risk only.
 */
public class LlmFallbackLayer implements DecideLayer {

  private final boolean enabled;

  public LlmFallbackLayer() {
    this(false);
  }

  public LlmFallbackLayer(boolean enabled) {
    this.enabled = enabled;
  }

  public boolean enabled() {
    return enabled;
  }

  @Override
  public Optional<DecideResult> apply(DecideRequest request, List<RouteRow> eligible) {
    if (!enabled) {
      return Optional.empty();
    }
    if (eligible.isEmpty()) {
      return Optional.empty();
    }
    /*
     * Prod (I12) — still not a Pattern 0 route. Pseudocode:
     *
     *   ids = eligible.map(route_id)          // never the full catalogue
     *   system = "Choose only among these route_id values. Reply JSON only."
     *   user   = message
     *            + ids
     *            + optional ② top-k (intent_label, route_id)
     *
     *   POST {gateway}/v1/chat/completions    // same OpenAI-shaped egress Runtime uses
     *     model: lightweight / JSON mode
     *     timeout: 400–800 ms (not AR's generate timeout)
     *     retry: none
     *
     *   parse JSON:
     *     { "outcome": "route", "route_id": "fee_explain" }
     *     { "outcome": "clarify", "candidates": ["fee_explain", "product_explain"] }
     *     { "outcome": "abstain" }
     *
     *   return restrictToEligible(parsed, eligible)
     *   on timeout / 5xx / invalid JSON → Optional.empty()  // orchestrator abstains
     *
     * Flag stays off until I12. Do not call Runtime POST /v1/runs.
     */
    return Optional.empty();
  }

  /** Port contract: a model id outside eligible becomes abstain, never a silent route. */
  static DecideResult restrictToEligible(DecideResult proposed, List<RouteRow> eligible) {
    List<String> ids = LayerIds.of(eligible);
    Set<String> allowed = Set.copyOf(ids);
    if ("route".equals(proposed.outcome())) {
      if (proposed.routeId() == null || !allowed.contains(proposed.routeId())) {
        return DecideResult.abstain(ids);
      }
      RouteRow row =
          eligible.stream()
              .filter(candidate -> candidate.routeId().equals(proposed.routeId()))
              .findFirst()
              .orElseThrow();
      return DecideResult.route(row, proposed.confidence() == null ? 0.5 : proposed.confidence(), ids);
    }
    if ("clarify".equals(proposed.outcome())) {
      List<Map<String, Object>> kept = new ArrayList<>();
      if (proposed.candidates() != null) {
        for (Map<String, Object> candidate : proposed.candidates()) {
          Object id = candidate.get("route_id");
          if (id instanceof String routeId && allowed.contains(routeId)) {
            kept.add(new LinkedHashMap<>(candidate));
          }
        }
      }
      if (kept.isEmpty()) {
        return DecideResult.abstain(ids);
      }
      String prompt =
          proposed.clarifyPrompt() == null
              ? "Which of these did you mean?"
              : proposed.clarifyPrompt();
      return DecideResult.clarify(prompt, kept, ids);
    }
    return DecideResult.abstain(ids);
  }
}
