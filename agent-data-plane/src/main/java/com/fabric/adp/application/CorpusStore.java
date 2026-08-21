package com.fabric.adp.application;

import com.fabric.adp.domain.Corpus;
import java.util.List;
import java.util.Optional;

public interface CorpusStore {

  Optional<Corpus> find(String corpusId);

  List<Corpus> listPublished();

  List<Corpus> listAll();
}
