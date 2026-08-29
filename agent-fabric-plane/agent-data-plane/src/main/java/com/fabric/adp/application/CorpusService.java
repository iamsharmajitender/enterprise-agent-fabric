package com.fabric.adp.application;

import com.fabric.adp.domain.Corpus;
import com.fabric.adp.domain.NotFoundException;
import java.util.List;

public class CorpusService {

  private final CorpusStore store;

  public CorpusService(CorpusStore store) {
    this.store = store;
  }

  public Corpus get(String corpusId) {
    return store.find(corpusId).orElseThrow(() -> new NotFoundException(corpusId));
  }

  public List<Corpus> listPublished() {
    return store.listPublished();
  }

  public List<Corpus> listAll() {
    return store.listAll();
  }
}
