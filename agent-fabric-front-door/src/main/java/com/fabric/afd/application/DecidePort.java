package com.fabric.afd.application;

import com.fabric.afd.domain.DecideCall;
import com.fabric.afd.domain.DecideOutcome;

public interface DecidePort {
  DecideOutcome decide(DecideCall call);
}
