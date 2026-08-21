package com.fabric.adp.application;

import com.fabric.adp.domain.NotFoundException;
import com.fabric.adp.domain.PromptPack;
import java.util.List;

public class PromptService {

  private final PromptStore store;

  public PromptService(PromptStore store) {
    this.store = store;
  }

  public PromptPack get(String promptId, String promptVersion) {
    return store
        .find(promptId, promptVersion)
        .orElseThrow(() -> new NotFoundException(promptId + "@" + promptVersion));
  }

  public PromptPack published(String promptId) {
    return store
        .findPublished(promptId)
        .or(() -> store.listVersions(promptId).stream().findFirst())
        .orElseThrow(() -> new NotFoundException(promptId));
  }

  public List<PromptPack> listPublished() {
    return store.listPublished();
  }

  public List<PromptPack> listAll() {
    return store.listAll();
  }

  public List<PromptPack> versions(String promptId) {
    List<PromptPack> found = store.listVersions(promptId);
    if (found.isEmpty()) {
      throw new NotFoundException(promptId);
    }
    return found;
  }
}
