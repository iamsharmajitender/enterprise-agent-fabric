package com.fabric.adp.application;

/** Seed corpus search gateway URLs (Compose network hostnames). */
public final class CorpusGatewayUrls {

  /** Shared assistant / policy prefetch gateway. */
  public static final String ASSISTANT =
      "http://agent-mocks:3010/v1/search/assistant";

  /** Shared legal retrieve gateway. */
  public static final String LEGAL = "http://agent-mocks:3010/v1/search/legal";

  /** Shared KYC / sanctions gateway. */
  public static final String KYC = "http://agent-mocks:3010/v1/search/kyc";

  /** Dedicated gateway for one corpus (collection still names the index). */
  public static String dedicated(String corpusId) {
    return "http://agent-mocks:3010/corpora/" + corpusId + "/search";
  }

  private CorpusGatewayUrls() {}
}
