package com.fabric.adp.application;

import com.fabric.adp.domain.NotFoundException;
import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Set;

public class CatalogueService {

  private final RouteStore store;

  public CatalogueService(RouteStore store) {
    this.store = store;
  }

  public List<RouteRow> list() {
    return store.activeRoutes();
  }

  public List<RouteRow> listAll() {
    return store.allRoutes();
  }

  public RouteRow get(String routeId, String versionOrNull) {
    if (versionOrNull == null || versionOrNull.isBlank()) {
      return store.activeRoute(routeId).orElseThrow(() -> new NotFoundException(routeId));
    }
    return store
        .route(routeId, versionOrNull)
        .orElseThrow(() -> new NotFoundException(routeId + "@" + versionOrNull));
  }

  public List<RouteRow> versions(String routeId) {
    List<RouteRow> rows = store.versions(routeId);
    if (rows.isEmpty()) {
      throw new NotFoundException(routeId);
    }
    return rows;
  }

  public List<RouteRow> eligible(String channel, Set<String> claims) {
    String ch = channel == null || channel.isBlank() ? "web" : channel;
    return list().stream()
        .filter(RouteRow::chatVisible)
        .filter(row -> row.channels().contains(ch))
        .filter(row -> claims.containsAll(row.requiredClaims()))
        .toList();
  }
}
