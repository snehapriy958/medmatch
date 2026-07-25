package com.medmatch.auth.repository;

import java.time.LocalDateTime;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import com.medmatch.auth.audit.AuditAction;
import com.medmatch.auth.entity.AuditLog;


public interface AuditLogRepository extends JpaRepository<AuditLog, UUID> {

    /**
     * Returns paginated audit logs for a hospital.
     */
    Page<AuditLog> findByHospitalId(
            UUID hospitalId,
            Pageable pageable
    );


    /**
     * Returns paginated audit logs performed by a user.
     */
    Page<AuditLog> findByPerformedById(
            UUID performedById,
            Pageable pageable
    );


    /**
     * Returns paginated audit logs for a specific action.
     */
    Page<AuditLog> findByAction(
            AuditAction action,
            Pageable pageable
    );


    /**
     * Returns paginated audit logs for a specific resource.
     */
    Page<AuditLog> findByResourceTypeAndResourceId(
            String resourceType,
            UUID resourceId,
            Pageable pageable
    );


    /**
     * Returns paginated audit logs created after the specified timestamp.
     */
    Page<AuditLog> findByCreatedAtAfter(
            LocalDateTime createdAt,
            Pageable pageable
    );

}