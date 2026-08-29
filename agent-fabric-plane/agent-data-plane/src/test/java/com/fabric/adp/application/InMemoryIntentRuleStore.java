package com.fabric.adp.application;

import com.fabric.adp.domain.IntentRule;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

public class InMemoryIntentRuleStore implements IntentRuleStore {

  private final List<IntentRule> rules = new CopyOnWriteArrayList<>();

  public InMemoryIntentRuleStore seedDemo() {
    rules.add(new IntentRule("cmd-shopassist", "command", "/shopassist", "shopassist_case", 10));
    return this;
  }

  @Override
  public List<IntentRule> list() {
    return rules.stream()
        .sorted(Comparator.comparingInt(IntentRule::sortOrder).thenComparing(IntentRule::ruleId))
        .toList();
  }
}
