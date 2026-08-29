package com.fabric.adp.domain;

import java.util.List;

public record MemoryProfile(
    String conversation,
    String working,
    String loop,
    String longTerm,
    Integer ttlHours,
    List<String> isolation) {}
