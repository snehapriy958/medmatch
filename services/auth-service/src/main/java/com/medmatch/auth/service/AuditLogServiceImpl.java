package com.medmatch.auth.service;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.medmatch.auth.audit.AuditAction;
import com.medmatch.auth.entity.AuditLog;
import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.repository.AuditLogRepository;

@Service
@Transactional
public class AuditLogServiceImpl implements AuditLogService {

    private final AuditLogRepository auditLogRepository;


    public AuditLogServiceImpl(
            AuditLogRepository auditLogRepository
    ) {
        this.auditLogRepository = auditLogRepository;
    }


    /**
     * Creates and stores an audit log entry.
     */
    @Override
    public AuditLog log(
            AuditAction action,
            String resourceType,
            UUID resourceId,
            User performedBy,
            Hospital hospital,
            String details,
            String ipAddress
    ) {

        AuditLog auditLog = new AuditLog(
                action.name(),
                resourceType,
                resourceId,
                performedBy.getId(),
                performedBy.getUsername(),
                performedBy.getRole().name(),
                hospital.getId(),
                hospital.getName(),
                details,
                ipAddress
        );

        return auditLogRepository.save(auditLog);
    }


    /**
     * Returns all audit logs.
     */
    @Override
    @Transactional(readOnly = true)
    public Page<AuditLog> getAllAuditLogs(
            Pageable pageable
    ) {
        return auditLogRepository.findAll(pageable);
    }


    /**
     * Returns audit logs for a hospital.
     */
    @Override
    @Transactional(readOnly = true)
    public Page<AuditLog> getHospitalAuditLogs(
            UUID hospitalId,
            Pageable pageable
    ) {
        return auditLogRepository.findByHospitalId(
                hospitalId,
                pageable
        );
    }


    /**
     * Returns audit logs for a user.
     */
    @Override
    @Transactional(readOnly = true)
    public Page<AuditLog> getUserAuditLogs(
            UUID userId,
            Pageable pageable
    ) {
        return auditLogRepository.findByPerformedById(
                userId,
                pageable
        );
    }


    /**
     * Returns audit logs filtered by action.
     */
    @Override
    @Transactional(readOnly = true)
    public Page<AuditLog> getAuditLogsByAction(
            AuditAction action,
            Pageable pageable
    ) {
        return auditLogRepository.findByAction(
                action,
                pageable
        );
    }


    /**
     * Returns audit logs for a specific resource.
     */
    @Override
    @Transactional(readOnly = true)
    public Page<AuditLog> getAuditLogsByResource(
            String resourceType,
            UUID resourceId,
            Pageable pageable
    ) {
        return auditLogRepository.findByResourceTypeAndResourceId(
                resourceType,
                resourceId,
                pageable
        );
    }
}