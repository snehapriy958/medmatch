package com.medmatch.auth.dto;

import java.time.LocalDateTime;
import java.util.UUID;

public record AuditLogResponse(

        UUID id,

        String action,

        String resourceType,

        UUID resourceId,

        String performedByUsername,

        String performedByRole,

        String hospitalName,

        String details,

        String ipAddress,

        LocalDateTime createdAt

) {
}