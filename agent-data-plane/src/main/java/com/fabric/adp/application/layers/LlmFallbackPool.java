package com.fabric.adp.application.layers;

import com.fabric.adp.domain.DecideResult;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Separate Layer ③ pool. Queue length 0 (SynchronousQueue + abort): saturate sheds, does not line
 * up behind ②. {@link #invoke} applies a hard timeout and does not retry.
 */
public final class LlmFallbackPool {

  private LlmFallbackPool() {}

  public static ExecutorService create() {
    AtomicInteger n = new AtomicInteger();
    ThreadFactory factory =
        task -> {
          Thread thread = new Thread(task, "adp-layer-3-" + n.incrementAndGet());
          thread.setDaemon(true);
          return thread;
        };
    return new ThreadPoolExecutor(
        2,
        2,
        60,
        TimeUnit.SECONDS,
        new SynchronousQueue<>(),
        factory,
        new ThreadPoolExecutor.AbortPolicy());
  }

  public static Optional<DecideResult> invoke(
      ExecutorService pool,
      long timeoutMs,
      Callable<Optional<DecideResult>> task,
      List<String> eligibleIds) {
    Future<Optional<DecideResult>> future;
    try {
      future = pool.submit(task);
    } catch (RejectedExecutionException e) {
      return Optional.of(DecideResult.abstain(eligibleIds));
    }
    try {
      Optional<DecideResult> decided = future.get(timeoutMs, TimeUnit.MILLISECONDS);
      return decided == null ? Optional.empty() : decided;
    } catch (TimeoutException e) {
      future.cancel(true);
      return Optional.of(DecideResult.abstain(eligibleIds));
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      future.cancel(true);
      return Optional.of(DecideResult.abstain(eligibleIds));
    } catch (ExecutionException e) {
      return Optional.of(DecideResult.abstain(eligibleIds));
    }
  }
}
