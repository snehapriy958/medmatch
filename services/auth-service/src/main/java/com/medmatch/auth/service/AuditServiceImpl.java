package com.medmatch.auth.service;

import com.medmatch.auth.entity.AuditLog;
import com.medmatch.auth.repository.AuditLogRepository;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AuditServiceImpl implements AuditService {

    private final AuditLogRepository auditLogRepository;

    @Override
    @Transactional
    public void createAuditLog(
            UUID userId,
            String action,
            String resourceType,
            UUID resourceId,
            String description
    ) {

        AuditLog auditLog = AuditLog.builder()
                .performedById(userId)
                .action(action)
                .resourceType(resourceType)
                .resourceId(resourceId)
                .details(description)
                .build();

        auditLogRepository.save(auditLog);
    }


    @Override
    @Transactional(readOnly = true)
    public List<AuditLog> getUserAuditLogs(UUID userId) {

        return auditLogRepository.findByPerformedById(userId);
    }
}