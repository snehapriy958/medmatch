package com.medmatch.auth.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

// NOTE: audit_logs is a shared table, physically owned (migrated) by
// auth-service via Flyway, but also written directly by the AI service
// (see services/ai-service/app/models/audit_log.py and
// app/repositories/audit_log_repository.py). The physical table has
// 12 columns; this entity intentionally maps only the 8 that
// auth-service itself uses.
//
// The 4 columns below are NOT mapped here and are always NULL on rows
// written by auth-service. They are nullable, ai-service-only columns,
// populated exclusively by the AI service from JWT claims at write time:
//   - performed_by_username (varchar(255))
//   - performed_by_role     (varchar(50))
//   - hospital_id           (uuid)
//   - hospital_name         (varchar(255))
//
// This is a deliberate minimal-compatibility choice, not an oversight.
// Hibernate's ddl-auto=validate only checks columns this entity maps,
// so leaving these unmapped is safe as long as `action` and
// `resource_type` declare the same lengths as the physical column
// (see V4__create_audit_logs_table.sql). Full Java-side parity
// (mapping these fields and extending AuditService.createAuditLog)
// is a possible future change, not implemented in this phase.
@Entity
@Table(name = "audit_logs")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @JdbcTypeCode(SqlTypes.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    // Stored as a raw UUID column, not a @ManyToOne to User — keeps this
    // entity independent per the design requirement, and means audit
    // records survive even if the referenced User row is later deleted.
    @JdbcTypeCode(SqlTypes.UUID)
    @Column(name = "performed_by_id")
    private UUID performedById;

    @Column(name = "action", nullable = false, length = 100)
    private String action;

    @Column(name = "resource_type", length = 100)
    private String resourceType;

    @Column(name = "resource_id")
    private UUID resourceId;

    @Column(name = "ip_address")
    private String ipAddress;

    @Column(name = "details", columnDefinition = "TEXT")
    private String details;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}