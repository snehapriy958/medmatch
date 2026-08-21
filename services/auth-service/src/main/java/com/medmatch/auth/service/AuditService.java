package com.medmatch.auth.service;

import com.medmatch.auth.entity.AuditLog;

import java.util.List;
import java.util.UUID;

public interface AuditService {

    void createAuditLog(
            UUID userId,
            String action,
            String resourceType,
            UUID resourceId,
            String description
    );

    List<AuditLog> getUserAuditLogs(UUID userId);
}