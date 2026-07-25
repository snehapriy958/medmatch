package com.medmatch.auth.controller;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    private final JdbcTemplate jdbcTemplate;

    public HealthController(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {

        return Map.of(
                "status", "UP",
                "service", "auth-service",
                "timestamp", Instant.now().toString()
        );
    }

    @GetMapping("/health/live")
    public Map<String, Object> liveness() {

        return Map.of(
                "status", "UP",
                "service", "auth-service",
                "timestamp", Instant.now().toString()
        );
    }

    @GetMapping("/health/ready")
    public ResponseEntity<Map<String, Object>> readiness() {

        Map<String, String> checks = new LinkedHashMap<>();

        try {

            jdbcTemplate.queryForObject(
                    "SELECT 1",
                    Integer.class
            );

            checks.put("database", "UP");

        } catch (Exception ex) {

            checks.put("database", "DOWN");

            return ResponseEntity
                    .status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(Map.of(
                            "status", "DOWN",
                            "service", "auth-service",
                            "checks", checks,
                            "timestamp", Instant.now().toString()
                    ));
        }

        return ResponseEntity.ok(
                Map.of(
                        "status", "UP",
                        "service", "auth-service",
                        "checks", checks,
                        "timestamp", Instant.now().toString()
                )
        );
    }
}