package com.fabric.adp.application.layers;

import com.fabric.adp.domain.DecideRequest;
import com.fabric.adp.domain.DecideResult;
import com.fabric.adp.domain.RouteRow;
import java.util.List;
import java.util.Optional;

/**
 * One step in the decide pipeline. {@link Optional#empty()} means "I did not decide — try the next
 * layer." A present result (route, clarify, or abstain) stops the pipeline.
 */
public interface DecideLayer {

  Optional<DecideResult> apply(DecideRequest request, List<RouteRow> eligible);
}
