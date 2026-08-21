package com.medmatch.auth.repository;

import com.medmatch.auth.entity.AuditLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface AuditLogRepository extends JpaRepository<AuditLog, UUID> {

    List<AuditLog> findByPerformedById(UUID performedById);

    List<AuditLog> findTop50ByOrderByCreatedAtDesc();
    
    long countByAction(String action);
}