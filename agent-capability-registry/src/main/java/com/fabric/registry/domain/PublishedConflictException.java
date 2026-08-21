package com.fabric.registry.domain;

public class PublishedConflictException extends RuntimeException {

  public PublishedConflictException(String id, String version) {
    super("published version already exists: " + id + "@" + version);
  }
}
