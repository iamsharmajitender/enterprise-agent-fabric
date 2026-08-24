package com.fabric.adp.application.layers;

import static org.assertj.core.api.Assertions.assertThat;

import com.fabric.adp.domain.DecideResult;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class LlmFallbackPoolTest {

  private ExecutorService pool;

  @BeforeEach
  void setUp() {
    pool = LlmFallbackPool.create();
  }

  @AfterEach
  void tearDown() {
    pool.shutdownNow();
  }

  @Test
  void timeoutAbstainsWithoutWaitingForHungTask() throws Exception {
    long started = System.nanoTime();
    Optional<DecideResult> decided =
        LlmFallbackPool.invoke(
            pool,
            40,
            () -> {
              Thread.sleep(400);
              return Optional.empty();
            },
            List.of("fee_explain"));
    long elapsed = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started);
    assertThat(decided).isPresent();
    assertThat(decided.get().outcome()).isEqualTo("abstain");
    assertThat(elapsed).isLessThan(250L);
  }

  @Test
  void saturateShedsWithoutQueuing() throws Exception {
    CountDownLatch busy = new CountDownLatch(2);
    Runnable hang =
        () -> {
          busy.countDown();
          try {
            Thread.sleep(10_000);
          } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
          }
        };
    pool.submit(hang);
    pool.submit(hang);
    assertThat(busy.await(1, TimeUnit.SECONDS)).isTrue();

    long started = System.nanoTime();
    Optional<DecideResult> decided =
        LlmFallbackPool.invoke(pool, 500, Optional::empty, List.of("fee_explain"));
    long elapsed = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started);
    assertThat(decided).isPresent();
    assertThat(decided.get().outcome()).isEqualTo("abstain");
    assertThat(elapsed).isLessThan(200L);
  }
}
