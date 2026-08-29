package com.fabric.registry.adapters.in.http;

import com.fabric.registry.domain.NotFoundException;
import com.fabric.registry.domain.PublishedConflictException;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

  @ExceptionHandler(PublishedConflictException.class)
  ResponseEntity<Map<String, Object>> conflict(PublishedConflictException ex) {
    return ResponseEntity.status(HttpStatus.CONFLICT)
        .body(Map.of("error", Map.of("code", "PUBLISHED_EXISTS", "message", ex.getMessage())));
  }

  @ExceptionHandler(NotFoundException.class)
  ResponseEntity<Map<String, Object>> notFound(NotFoundException ex) {
    return ResponseEntity.status(HttpStatus.NOT_FOUND)
        .body(Map.of("error", Map.of("code", "NOT_FOUND", "message", ex.getMessage())));
  }
}
