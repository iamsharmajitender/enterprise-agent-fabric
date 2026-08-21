package com.fabric.afd.adapters.in.http;

import com.fabric.afd.domain.BadRequestException;
import com.fabric.afd.domain.ForbiddenException;
import com.fabric.afd.domain.NotFoundException;
import com.fabric.afd.domain.UnavailableException;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

  @ExceptionHandler(BadRequestException.class)
  ResponseEntity<Map<String, Object>> badRequest(BadRequestException ex) {
    return ResponseEntity.status(HttpStatus.BAD_REQUEST)
        .body(Map.of("error", Map.of("code", "BAD_REQUEST", "message", ex.getMessage())));
  }

  @ExceptionHandler(ForbiddenException.class)
  ResponseEntity<Map<String, Object>> forbidden(ForbiddenException ex) {
    return ResponseEntity.status(HttpStatus.FORBIDDEN)
        .body(Map.of("error", Map.of("code", "FORBIDDEN", "message", ex.getMessage())));
  }

  @ExceptionHandler(NotFoundException.class)
  ResponseEntity<Map<String, Object>> notFound(NotFoundException ex) {
    return ResponseEntity.status(HttpStatus.NOT_FOUND)
        .body(Map.of("error", Map.of("code", "NOT_FOUND", "message", ex.getMessage())));
  }

  @ExceptionHandler(UnavailableException.class)
  ResponseEntity<Map<String, Object>> unavailable(UnavailableException ex) {
    return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
        .body(Map.of("error", Map.of("code", "UNAVAILABLE", "message", ex.getMessage())));
  }
}
