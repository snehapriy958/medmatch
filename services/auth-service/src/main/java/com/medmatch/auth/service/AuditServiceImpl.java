package com.medmatch.auth.service;

import com.medmatch.auth.entity.AuditLog;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.AuditLogRepository;
import com.medmatch.auth.repository.UserRepository;

import lombok.RequiredArgsConstructor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AuditServiceImpl implements AuditService {

    private final AuditLogRepository auditLogRepository;
    private final UserRepository userRepository;


    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW)
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

        // NOTE: previously unguarded — AuditController allows
        // HOSPITAL_ADMIN here, but nothing stopped a HOSPITAL_ADMIN at
        // Hospital A from reading Hospital B users' full audit trails
        // by passing their id. Same tenant-boundary pattern as
        // UserServiceImpl. If the target user record no longer exists,
        // a non-admin caller is denied rather than allowed through —
        // the tenant boundary can't be verified, so this fails closed.
        Authentication authentication =
                SecurityContextHolder.getContext().getAuthentication();

        boolean isSystemAdmin = authentication.getAuthorities().stream()
                .anyMatch(authority ->
                        authority.getAuthority().equals("ROLE_SYSTEM_ADMIN"));

        if (!isSystemAdmin) {

            User currentUser = userRepository.findByEmail(authentication.getName())
                    .orElseThrow(() ->
                            new ResourceNotFoundException("Current user not found"));

            User targetUser = userRepository.findById(userId)
                    .orElseThrow(() ->
                            new AccessDeniedException(
                                    "Cannot access audit logs for this user"));

            if (!currentUser.getHospital().getId().equals(targetUser.getHospital().getId())) {

                throw new AccessDeniedException(
                        "Cannot access another hospital's audit logs");
            }
        }

        return auditLogRepository.findByPerformedById(userId);
    }
}