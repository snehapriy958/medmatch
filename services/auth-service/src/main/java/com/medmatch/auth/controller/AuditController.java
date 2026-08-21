package com.medmatch.auth.controller;

import com.medmatch.auth.entity.AuditLog;
import com.medmatch.auth.service.AuditService;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/audit-logs")
@RequiredArgsConstructor
public class AuditController {

    private final AuditService auditService;

    @GetMapping("/user/{userId}")
    @PreAuthorize("hasAnyRole('SYSTEM_ADMIN', 'HOSPITAL_ADMIN')")
    public ResponseEntity<List<AuditLog>> getUserAuditLogs(@PathVariable UUID userId) {
        return ResponseEntity.ok(auditService.getUserAuditLogs(userId));
    }
}