package com.fabric.adp.adapters.in.http;

import com.fabric.adp.domain.ForbiddenException;
import com.fabric.adp.domain.NotFoundException;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

  @ExceptionHandler(NotFoundException.class)
  ResponseEntity<Map<String, Object>> notFound(NotFoundException ex) {
    return ResponseEntity.status(HttpStatus.NOT_FOUND)
        .body(Map.of("error", Map.of("code", "NOT_FOUND", "message", ex.getMessage())));
  }

  @ExceptionHandler(ForbiddenException.class)
  ResponseEntity<Map<String, Object>> forbidden(ForbiddenException ex) {
    return ResponseEntity.status(HttpStatus.FORBIDDEN)
        .body(Map.of("error", Map.of("code", "FORBIDDEN", "message", ex.getMessage())));
  }
}
