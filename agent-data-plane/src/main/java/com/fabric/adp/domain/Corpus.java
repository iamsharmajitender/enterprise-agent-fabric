package com.fabric.adp.domain;

import java.time.Instant;

public record Corpus(
    String corpusId,
    String displayName,
    String url,
    String collection,
    String auth,
    String owner,
    String status,
    String region,
    Instant updatedAt) {}
