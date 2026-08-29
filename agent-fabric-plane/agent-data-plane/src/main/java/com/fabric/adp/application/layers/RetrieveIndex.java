package com.fabric.adp.application.layers;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * In-process kNN over labelled seed utterances. Not {@code RouteRow.keywords}. Neighbors whose
 * {@code route_id} is outside eligible are dropped before scoring.
 */
public final class RetrieveIndex {

  static final double OOD_THRESHOLD = 0.28;
  static final double TIE_MARGIN = 0.12;

  private static final String RESOURCE = "/retrieve/utterances.json";
  private static final Pattern TOKEN = Pattern.compile("[a-z0-9]+");
  private static final Set<String> STOP =
      Set.of(
          "a", "an", "the", "to", "of", "for", "on", "in", "is", "was", "were", "be", "i", "my",
          "me", "we", "you", "your", "this", "that", "these", "those", "please", "about", "with",
          "and", "or", "did", "do", "does", "what", "why", "how", "it");
  private static final ObjectMapper MAPPER =
      new ObjectMapper()
          .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
          .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

  private final Map<String, List<Set<String>>> docsByRoute;

  public RetrieveIndex(List<RetrieveUtterance> utterances) {
    Map<String, List<Set<String>>> byRoute = new HashMap<>();
    for (RetrieveUtterance utterance : utterances) {
      if (utterance.routeId() == null || utterance.routeId().isBlank()) {
        continue;
      }
      Set<String> tokens = tokens(utterance.text());
      if (tokens.isEmpty()) {
        continue;
      }
      byRoute.computeIfAbsent(utterance.routeId(), id -> new ArrayList<>()).add(tokens);
    }
    this.docsByRoute = Map.copyOf(byRoute);
  }

  public static RetrieveIndex loadDefault() {
    try (InputStream in = RetrieveIndex.class.getResourceAsStream(RESOURCE)) {
      if (in == null) {
        throw new IllegalStateException("missing retrieve index: " + RESOURCE);
      }
      RetrieveUtteranceFile file = MAPPER.readValue(in, RetrieveUtteranceFile.class);
      List<RetrieveUtterance> utterances =
          file.utterances() == null ? List.of() : file.utterances();
      return new RetrieveIndex(utterances);
    } catch (IOException e) {
      throw new UncheckedIOException(RESOURCE, e);
    }
  }

  double bestScore(String message, String routeId) {
    List<Set<String>> docs = docsByRoute.get(routeId);
    if (docs == null || docs.isEmpty()) {
      return 0.0;
    }
    Set<String> query = tokens(message);
    if (query.isEmpty()) {
      return 0.0;
    }
    double best = 0.0;
    for (Set<String> doc : docs) {
      best = Math.max(best, cosine(query, doc));
    }
    return best;
  }

  static Set<String> tokens(String text) {
    if (text == null || text.isBlank()) {
      return Set.of();
    }
    Matcher matcher = TOKEN.matcher(text.toLowerCase(Locale.ROOT));
    Set<String> tokens = new LinkedHashSet<>();
    while (matcher.find()) {
      String token = matcher.group();
      if (!STOP.contains(token)) {
        tokens.add(token);
      }
    }
    return tokens;
  }

  static double cosine(Set<String> left, Set<String> right) {
    if (left.isEmpty() || right.isEmpty()) {
      return 0.0;
    }
    int overlap = 0;
    Set<String> smaller = left.size() <= right.size() ? left : right;
    Set<String> larger = smaller == left ? right : left;
    for (String token : smaller) {
      if (larger.contains(token)) {
        overlap++;
      }
    }
    if (overlap == 0) {
      return 0.0;
    }
    return overlap / Math.sqrt((double) left.size() * right.size());
  }

  public record RetrieveUtterance(String routeId, String text) {}

  public record RetrieveUtteranceFile(List<RetrieveUtterance> utterances) {}
}
