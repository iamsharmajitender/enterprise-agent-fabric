package com.fabric.adp.application;

import com.fabric.adp.domain.AutonomyPattern;
import com.fabric.adp.domain.MemoryProfile;
import com.fabric.adp.domain.ModelProfile;
import com.fabric.adp.domain.Retrieval;
import com.fabric.adp.domain.RouteRow;
import com.fabric.adp.domain.ToolManifest;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CopyOnWriteArrayList;

public class InMemoryRouteStore implements RouteStore {

  private static final String RUNS = "http://agent-runtime:3008/v1/runs";
  private static final String V = "2026.08.1";

  private final List<RouteRow> routes = new CopyOnWriteArrayList<>();

  public InMemoryRouteStore seedDemo() {
    add(
        "shopassist_case",
        1,
        "shopassist_case",
        "Pattern 1 (autonomous): ShopAssist front-line support. ASK for order/customer/email if missing, lookup order, then billing and policy domain APIs. Escalate when needed.",
        RUNS,
        InMemoryManifestStore.shopassistCase(),
        null,
        loopMemory("none", 24),
        "read_only_standard",
        ModelProfile.REASONING_STANDARD,
        null,
        "shopassist_case",
        null,
        null,
        12,
        "clarify",
        List.of("support:case"),
        List.of("web", "api"),
        true,
        List.of("damaged", "damage", "refund", "jacket", "charged twice", "duplicate charge", "ORD-77819"));
    return this;
  }

  public InMemoryRouteStore replace(RouteRow row) {
    routes.removeIf(
        existing ->
            existing.routeId().equals(row.routeId())
                && existing.routeVersion().equals(row.routeVersion()));
    routes.add(row);
    return this;
  }

  private void add(
      String id,
      int pattern,
      String intent,
      String description,
      String activation,
      ToolManifest manifest,
      Retrieval retrieval,
      MemoryProfile memory,
      String policy,
      ModelProfile model,
      String workflowId,
      String promptId,
      String outputSchema,
      String evalSuite,
      Integer maxLoop,
      String fallback,
      List<String> claims,
      List<String> channels,
      boolean chatVisible,
      List<String> keywords) {
    routes.add(
        new RouteRow(
            id,
            V,
            true,
            intent,
            description,
            activation,
            "agent-" + id,
            manifest,
            policy,
            model,
            retrieval,
            memory,
            workflowId,
            promptId,
            outputSchema,
            evalSuite,
            maxLoop,
            fallback,
            claims,
            channels,
            chatVisible,
            keywords,
            AutonomyPattern.fromCode(pattern)));
  }

  private static MemoryProfile conversationMemory() {
    return new MemoryProfile("session", "session", "none", "none", 24, List.of("tenant", "user", "session"));
  }

  private static MemoryProfile loopMemory() {
    return loopMemory("retrieve_only", 24);
  }

  private static MemoryProfile loopMemory(String longTerm, int ttlHours) {
    return new MemoryProfile(
        "session", "session", "checkpoint", longTerm, ttlHours, List.of("tenant", "user", "session"));
  }

  @Override
  public List<RouteRow> activeRoutes() {
    return routes.stream().filter(RouteRow::active).toList();
  }

  @Override
  public List<RouteRow> allRoutes() {
    return routes.stream()
        .sorted(
            Comparator.comparing(RouteRow::routeId)
                .thenComparing(Comparator.comparing(RouteRow::routeVersion).reversed()))
        .toList();
  }

  @Override
  public Optional<RouteRow> activeRoute(String routeId) {
    return routes.stream().filter(r -> r.routeId().equals(routeId) && r.active()).findFirst();
  }

  @Override
  public Optional<RouteRow> route(String routeId, String routeVersion) {
    return routes.stream()
        .filter(r -> r.routeId().equals(routeId) && r.routeVersion().equals(routeVersion))
        .findFirst();
  }

  @Override
  public List<RouteRow> versions(String routeId) {
    return routes.stream()
        .filter(r -> r.routeId().equals(routeId))
        .sorted(Comparator.comparing(RouteRow::routeVersion).reversed())
        .toList();
  }
}
