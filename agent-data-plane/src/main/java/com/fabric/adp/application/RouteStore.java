package com.fabric.adp.application;

import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Optional;

public interface RouteStore {

  List<RouteRow> activeRoutes();

  List<RouteRow> allRoutes();

  Optional<RouteRow> activeRoute(String routeId);

  Optional<RouteRow> route(String routeId, String routeVersion);

  List<RouteRow> versions(String routeId);
}
