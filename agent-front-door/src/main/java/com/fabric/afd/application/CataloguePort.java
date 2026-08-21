package com.fabric.afd.application;

import com.fabric.afd.domain.CatalogRoute;
import com.fabric.afd.domain.EligibleRoute;
import java.util.List;
import java.util.Map;

public interface CataloguePort {
  CatalogRoute get(String routeId, String routeVersion);

  List<EligibleRoute> eligible(String channel, Map<String, Object> claims);
}
