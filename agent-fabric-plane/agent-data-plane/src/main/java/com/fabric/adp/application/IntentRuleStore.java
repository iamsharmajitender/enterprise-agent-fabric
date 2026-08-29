package com.fabric.adp.application;

import com.fabric.adp.domain.IntentRule;
import java.util.List;

public interface IntentRuleStore {

  /** Rules in first-match order ({@code sort_order}, then {@code rule_id}). */
  List<IntentRule> list();
}
