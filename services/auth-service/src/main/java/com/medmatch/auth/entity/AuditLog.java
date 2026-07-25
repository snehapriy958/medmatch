package com.medmatch.auth.entity;

import java.time.LocalDateTime;
import java.util.UUID;

import com.medmatch.auth.audit.AuditAction;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;

@Entity
@Table(
        name = "audit_logs",
        indexes = {
                @Index(name = "idx_audit_created_at", columnList = "created_at"),
                @Index(name = "idx_audit_action", columnList = "action"),
                @Index(name = "idx_audit_resource_type", columnList = "resource_type"),
                @Index(name = "idx_audit_resource_id", columnList = "resource_id"),
                @Index(name = "idx_audit_user", columnList = "performed_by_id"),
                @Index(name = "idx_audit_hospital", columnList = "hospital_id")
        }
)
public class AuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;


    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 50)
    private AuditAction action;


    @Column(name = "resource_type", nullable = false, length = 100)
    private String resourceType;


    @Column(name = "resource_id", nullable = false)
    private UUID resourceId;


    @Column(name = "performed_by_id", nullable = false)
    private UUID performedById;


    @Column(name = "performed_by_username", nullable = false, length = 100)
    private String performedByUsername;


    @Column(name = "performed_by_role", nullable = false, length = 50)
    private String performedByRole;


    @Column(name = "hospital_id", nullable = false)
    private UUID hospitalId;


    @Column(name = "hospital_name", nullable = false, length = 255)
    private String hospitalName;


    @Column(length = 1000)
    private String details;


    @Column(name = "ip_address", length = 45)
    private String ipAddress;


    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;


    public AuditLog() {
    }


    public AuditLog(
            String action,
            String resourceType,
            UUID resourceId,
            UUID performedBy,
            String username,
            String role,
            UUID hospitalId,
            String hospitalName,
            String details,
            String ipAddress
    ) {
        this.action = AuditAction.valueOf(action);
        this.resourceType = resourceType;
        this.resourceId = resourceId;
        this.performedById = performedBy;
        this.performedByUsername = username;
        this.performedByRole = role;
        this.hospitalId = hospitalId;
        this.hospitalName = hospitalName;
        this.details = details;
        this.ipAddress = ipAddress;
    }


    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
    }


    public UUID getId() {
        return id;
    }


    public AuditAction getAction() {
        return action;
    }


    public void setAction(AuditAction action) {
        this.action = action;
    }


    public String getResourceType() {
        return resourceType;
    }


    public void setResourceType(String resourceType) {
        this.resourceType = resourceType;
    }


    public UUID getResourceId() {
        return resourceId;
    }


    public void setResourceId(UUID resourceId) {
        this.resourceId = resourceId;
    }


    public UUID getPerformedById() {
        return performedById;
    }


    public void setPerformedById(UUID performedById) {
        this.performedById = performedById;
    }


    public String getPerformedByUsername() {
        return performedByUsername;
    }


    public void setPerformedByUsername(String performedByUsername) {
        this.performedByUsername = performedByUsername;
    }


    public String getPerformedByRole() {
        return performedByRole;
    }


    public void setPerformedByRole(String performedByRole) {
        this.performedByRole = performedByRole;
    }


    public UUID getHospitalId() {
        return hospitalId;
    }


    public void setHospitalId(UUID hospitalId) {
        this.hospitalId = hospitalId;
    }


    public String getHospitalName() {
        return hospitalName;
    }


    public void setHospitalName(String hospitalName) {
        this.hospitalName = hospitalName;
    }


    public String getDetails() {
        return details;
    }


    public void setDetails(String details) {
        this.details = details;
    }


    public String getIpAddress() {
        return ipAddress;
    }


    public void setIpAddress(String ipAddress) {
        this.ipAddress = ipAddress;
    }


    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
}