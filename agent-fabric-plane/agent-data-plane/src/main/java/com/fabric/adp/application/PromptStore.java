package com.fabric.adp.application;

import com.fabric.adp.domain.PromptPack;
import java.util.List;
import java.util.Optional;

public interface PromptStore {

  Optional<PromptPack> find(String promptId, String promptVersion);

  Optional<PromptPack> findPublished(String promptId);

  List<PromptPack> listPublished();

  List<PromptPack> listAll();

  List<PromptPack> listVersions(String promptId);
}
