package com.medmatch.auth.controller;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.medmatch.auth.audit.AuditAction;
import com.medmatch.auth.dto.AuditLogResponse;
import com.medmatch.auth.mapper.AuditLogMapper;
import com.medmatch.auth.service.AuditLogService;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;


@Validated
@RestController
@RequestMapping("/auth/audit-logs")
@PreAuthorize("hasRole('ADMIN')")
public class AuditLogController {

    private final AuditLogService auditLogService;
    private final AuditLogMapper auditLogMapper;


    public AuditLogController(
            AuditLogService auditLogService,
            AuditLogMapper auditLogMapper
    ) {
        this.auditLogService = auditLogService;
        this.auditLogMapper = auditLogMapper;
    }


    /**
     * Returns all audit logs.
     */
    @GetMapping
    public ResponseEntity<Page<AuditLogResponse>> getAllAuditLogs(

            @RequestParam(defaultValue = "0")
            @Min(0)
            int page,

            @RequestParam(defaultValue = "20")
            @Min(1)
            @Max(100)
            int size

    ) {

        PageRequest pageable = PageRequest.of(
                page,
                size,
                Sort.by("createdAt").descending()
        );


        Page<AuditLogResponse> response =
                auditLogService
                        .getAllAuditLogs(pageable)
                        .map(auditLogMapper::toResponse);


        return ResponseEntity.ok(response);
    }


    /**
     * Returns audit logs filtered by action.
     */
    @GetMapping("/action/{action}")
    public ResponseEntity<Page<AuditLogResponse>> getAuditLogsByAction(

            @PathVariable AuditAction action,

            @RequestParam(defaultValue = "0")
            @Min(0)
            int page,

            @RequestParam(defaultValue = "20")
            @Min(1)
            @Max(100)
            int size

    ) {

        PageRequest pageable = PageRequest.of(
                page,
                size,
                Sort.by("createdAt").descending()
        );


        Page<AuditLogResponse> response =
                auditLogService
                        .getAuditLogsByAction(action, pageable)
                        .map(auditLogMapper::toResponse);


        return ResponseEntity.ok(response);
    }


    /**
     * Returns audit logs for a user.
     */
    @GetMapping("/user/{userId}")
    public ResponseEntity<Page<AuditLogResponse>> getUserAuditLogs(

            @PathVariable UUID userId,

            @RequestParam(defaultValue = "0")
            @Min(0)
            int page,

            @RequestParam(defaultValue = "20")
            @Min(1)
            @Max(100)
            int size

    ) {

        PageRequest pageable = PageRequest.of(
                page,
                size,
                Sort.by("createdAt").descending()
        );


        Page<AuditLogResponse> response =
                auditLogService
                        .getUserAuditLogs(userId, pageable)
                        .map(auditLogMapper::toResponse);


        return ResponseEntity.ok(response);
    }


    /**
     * Returns audit logs for a hospital.
     */
    @GetMapping("/hospital/{hospitalId}")
    public ResponseEntity<Page<AuditLogResponse>> getHospitalAuditLogs(

            @PathVariable UUID hospitalId,

            @RequestParam(defaultValue = "0")
            @Min(0)
            int page,

            @RequestParam(defaultValue = "20")
            @Min(1)
            @Max(100)
            int size

    ) {

        PageRequest pageable = PageRequest.of(
                page,
                size,
                Sort.by("createdAt").descending()
        );


        Page<AuditLogResponse> response =
                auditLogService
                        .getHospitalAuditLogs(hospitalId, pageable)
                        .map(auditLogMapper::toResponse);


        return ResponseEntity.ok(response);
    }
}