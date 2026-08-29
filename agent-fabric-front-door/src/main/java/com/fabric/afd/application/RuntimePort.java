package com.fabric.afd.application;

import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.RunStart;
import java.util.Map;
import java.util.Optional;

public interface RuntimePort {
  String start(RunStart start);

  Map<String, Object> status(String correlationId);

  void resume(String correlationId, String message);

  Optional<FrozenRoute> openRun(String sessionId);
}
