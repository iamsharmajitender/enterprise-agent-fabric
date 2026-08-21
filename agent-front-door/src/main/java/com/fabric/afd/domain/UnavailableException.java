package com.fabric.afd.domain;

public class UnavailableException extends RuntimeException {
  public UnavailableException(String message) {
    super(message);
  }

  public UnavailableException(String message, Throwable cause) {
    super(message, cause);
  }
}
