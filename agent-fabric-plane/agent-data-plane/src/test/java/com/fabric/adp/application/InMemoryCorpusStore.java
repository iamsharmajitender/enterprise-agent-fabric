package com.fabric.adp.application;

import com.fabric.adp.domain.Corpus;
import java.time.Instant;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class InMemoryCorpusStore implements CorpusStore {

  private static final Instant UPDATED = Instant.parse("2026-08-21T00:00:00Z");

  private final Map<String, Corpus> rows = new LinkedHashMap<>();

  public InMemoryCorpusStore seedDemo() {
    put(policyEngine());
    put(clauseIndex());
    put(legalPlaybook());
    put(productFaq());
    put(accounts());
    put(sanctionsLists());
    put(kycPolicy());
    put(researchIndexDraft());
    put(new Corpus(
        "product-terms",
        "Product terms",
        CorpusGatewayUrls.dedicated("product-terms"),
        "product-terms",
        "workload-oauth",
        "product",
        "published",
        null,
        UPDATED));
    put(new Corpus(
        "fee-schedule",
        "Fee schedule",
        CorpusGatewayUrls.dedicated("fee-schedule"),
        "fee-schedule",
        "workload-oauth",
        "product",
        "published",
        null,
        UPDATED));
    put(new Corpus(
        "product-disclosure",
        "Product disclosure",
        CorpusGatewayUrls.dedicated("product-disclosure"),
        "product-disclosure",
        "workload-oauth",
        "product",
        "published",
        null,
        UPDATED));
    return this;
  }

  public InMemoryCorpusStore seedEvalBoard() {
    return seedDemo();
  }

  public static Corpus policyEngine() {
    return new Corpus(
        "policy-engine",
        "Policy engine",
        CorpusGatewayUrls.ASSISTANT,
        "policy-engine",
        "workload-oauth",
        "policy-ops",
        "published",
        null,
        UPDATED);
  }

  public static Corpus clauseIndex() {
    return new Corpus(
        "clause-index",
        "Clause index",
        CorpusGatewayUrls.LEGAL,
        "clause-index",
        "workload-oauth",
        "legal",
        "published",
        null,
        UPDATED);
  }

  public static Corpus legalPlaybook() {
    return new Corpus(
        "legal-playbook",
        "Legal playbook",
        CorpusGatewayUrls.LEGAL,
        "legal-playbook",
        "workload-oauth",
        "legal",
        "published",
        null,
        UPDATED);
  }

  private static Corpus productFaq() {
    return new Corpus(
        "product-faq",
        "Product FAQ",
        CorpusGatewayUrls.ASSISTANT,
        "product-faq",
        "workload-oauth",
        "assistant-platform",
        "published",
        null,
        UPDATED);
  }

  private static Corpus accounts() {
    return new Corpus(
        "accounts",
        "Accounts",
        CorpusGatewayUrls.ASSISTANT,
        "accounts",
        "workload-oauth",
        "assistant-platform",
        "published",
        null,
        UPDATED);
  }

  private static Corpus sanctionsLists() {
    return new Corpus(
        "sanctions-lists",
        "Sanctions lists",
        CorpusGatewayUrls.KYC,
        "sanctions-lists",
        "workload-oauth",
        "kyc-ops",
        "published",
        null,
        UPDATED);
  }

  private static Corpus kycPolicy() {
    return new Corpus(
        "kyc-policy",
        "KYC policy",
        CorpusGatewayUrls.KYC,
        "kyc-policy",
        "workload-oauth",
        "kyc-ops",
        "published",
        null,
        UPDATED);
  }

  public static Corpus researchIndexDraft() {
    return new Corpus(
        "research-index",
        "Research index",
        CorpusGatewayUrls.dedicated("research-index"),
        "research-index",
        "workload-oauth",
        "assistant-platform",
        "draft",
        null,
        UPDATED);
  }

  private void put(Corpus corpus) {
    rows.put(corpus.corpusId(), corpus);
  }

  @Override
  public Optional<Corpus> find(String corpusId) {
    return Optional.ofNullable(rows.get(corpusId));
  }

  @Override
  public List<Corpus> listPublished() {
    return rows.values().stream()
        .filter(row -> "published".equals(row.status()))
        .sorted(Comparator.comparing(Corpus::corpusId))
        .toList();
  }

  @Override
  public List<Corpus> listAll() {
    return rows.values().stream().sorted(Comparator.comparing(Corpus::corpusId)).toList();
  }
}
