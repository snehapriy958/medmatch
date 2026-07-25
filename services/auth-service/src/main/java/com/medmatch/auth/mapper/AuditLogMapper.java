package com.medmatch.auth.mapper;

import org.springframework.stereotype.Component;

import com.medmatch.auth.dto.AuditLogResponse;
import com.medmatch.auth.entity.AuditLog;

@Component
public class AuditLogMapper {

    public AuditLogResponse toResponse(AuditLog auditLog) {

        return new AuditLogResponse(
                auditLog.getId(),
                auditLog.getAction().name(),
                auditLog.getResourceType(),
                auditLog.getResourceId(),
                auditLog.getPerformedByUsername(),
                auditLog.getPerformedByRole(),
                auditLog.getHospitalName(),
                auditLog.getDetails(),
                auditLog.getIpAddress(),
                auditLog.getCreatedAt()
        );
    }

}