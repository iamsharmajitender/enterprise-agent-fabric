package com.fabric.adp.adapters.in.http;

import com.fabric.adp.domain.Corpus;
import java.util.LinkedHashMap;
import java.util.Map;

final class CorpusBodies {

  private CorpusBodies() {}

  static Map<String, Object> toBody(Corpus corpus) {
    if (corpus == null) {
      return null;
    }
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("corpus_id", corpus.corpusId());
    body.put("display_name", corpus.displayName());
    body.put("url", corpus.url());
    body.put("collection", corpus.collection());
    body.put("auth", corpus.auth());
    body.put("owner", corpus.owner());
    body.put("status", corpus.status());
    body.put("region", corpus.region());
    body.put("updated_at", corpus.updatedAt());
    return body;
  }
}
