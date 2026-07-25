package com.medmatch.auth.service;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import com.medmatch.auth.audit.AuditAction;
import com.medmatch.auth.entity.AuditLog;
import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.User;


public interface AuditLogService {


    AuditLog log(
            AuditAction action,
            String resourceType,
            UUID resourceId,
            User performedBy,
            Hospital hospital,
            String details,
            String ipAddress
    );


    Page<AuditLog> getAllAuditLogs(
            Pageable pageable
    );


    Page<AuditLog> getHospitalAuditLogs(
            UUID hospitalId,
            Pageable pageable
    );


    Page<AuditLog> getUserAuditLogs(
            UUID userId,
            Pageable pageable
    );


    Page<AuditLog> getAuditLogsByAction(
            AuditAction action,
            Pageable pageable
    );


    Page<AuditLog> getAuditLogsByResource(
            String resourceType,
            UUID resourceId,
            Pageable pageable
    );

}