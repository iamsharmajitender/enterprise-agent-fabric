package com.fabric.afd.application;

import com.fabric.afd.domain.FrozenRoute;
import com.fabric.afd.domain.RunStart;
import java.util.Map;
import java.util.Optional;

public interface RuntimePort {
  String start(RunStart start);

  Map<String, Object> status(String correlationId, String activationTarget);

  void resume(String correlationId, String message, String activationTarget);

  Optional<FrozenRoute> openRun(String sessionId);
}
