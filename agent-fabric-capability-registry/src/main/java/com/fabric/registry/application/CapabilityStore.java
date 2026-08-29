package com.fabric.registry.application;

import com.fabric.registry.domain.CapabilityVersion;
import java.util.List;
import java.util.Optional;

public interface CapabilityStore {

  Optional<CapabilityVersion> find(String id, String version);

  void upsert(CapabilityVersion capability);

  List<CapabilityVersion> listPublished(String query);

  List<CapabilityVersion> listAll(String query);

  List<CapabilityVersion> listVersions(String id);
}
