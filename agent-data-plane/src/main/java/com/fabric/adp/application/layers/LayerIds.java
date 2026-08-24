package com.fabric.adp.application.layers;

import com.fabric.adp.domain.RouteRow;
import java.util.List;

final class LayerIds {

  private LayerIds() {}

  static List<String> of(List<RouteRow> rows) {
    return rows.stream().map(RouteRow::routeId).toList();
  }
}
