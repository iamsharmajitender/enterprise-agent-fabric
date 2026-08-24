package com.fabric.adp.application;

import com.fabric.adp.domain.IntentRule;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

public class InMemoryIntentRuleStore implements IntentRuleStore {

  private final List<IntentRule> rules = new CopyOnWriteArrayList<>();

  public InMemoryIntentRuleStore seedDemo() {
    rules.add(new IntentRule("cmd-hr", "command", "/hr", "agent-chat", 10));
    rules.add(new IntentRule("cmd-human", "command", "talk to a human", "agent-chat", 20));
    rules.add(new IntentRule("cmd-freeze", "command", "/freeze", "card_freeze", 30));
    return this;
  }

  @Override
  public List<IntentRule> list() {
    return rules.stream()
        .sorted(Comparator.comparingInt(IntentRule::sortOrder).thenComparing(IntentRule::ruleId))
        .toList();
  }
}
