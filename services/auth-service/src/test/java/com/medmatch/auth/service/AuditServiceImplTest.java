package com.medmatch.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.medmatch.auth.entity.AuditLog;
import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.RoleType;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.repository.AuditLogRepository;
import com.medmatch.auth.repository.UserRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

@ExtendWith(MockitoExtension.class)
class AuditServiceImplTest {

    @Mock private AuditLogRepository auditLogRepository;
    @Mock private UserRepository userRepository;

    @InjectMocks
    private AuditServiceImpl auditService;

    private Hospital hospitalA;
    private Hospital hospitalB;
    private User adminAtHospitalA;
    private User targetAtHospitalA;
    private User targetAtHospitalB;

    @BeforeEach
    void setUp() {
        hospitalA = Hospital.builder().id(UUID.randomUUID()).code("HOSP_A").name("Hospital A").build();
        hospitalB = Hospital.builder().id(UUID.randomUUID()).code("HOSP_B").name("Hospital B").build();
        Role role = Role.builder().id(UUID.randomUUID()).name(RoleType.HOSPITAL_ADMIN).build();

        adminAtHospitalA = User.builder()
                .id(UUID.randomUUID()).email("admin@hospa.org").role(role).hospital(hospitalA).build();
        targetAtHospitalA = User.builder()
                .id(UUID.randomUUID()).email("colleague@hospa.org").role(role).hospital(hospitalA).build();
        targetAtHospitalB = User.builder()
                .id(UUID.randomUUID()).email("stranger@hospb.org").role(role).hospital(hospitalB).build();
    }

    @AfterEach
    void clearContext() {
        SecurityContextHolder.clearContext();
    }

    private void authenticateAs(User caller, RoleType role) {
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(
                        caller.getEmail(), null,
                        List.of(new SimpleGrantedAuthority("ROLE_" + role.name()))));
    }

    // --- createAuditLog ---

    @Test
    void createAuditLog_buildsAndSavesEntryWithGivenFields() {
        UUID userId = UUID.randomUUID();
        UUID resourceId = UUID.randomUUID();

        auditService.createAuditLog(userId, "LOGIN_SUCCESS", "USER", resourceId, "User logged in");

        ArgumentCaptor<AuditLog> captor = ArgumentCaptor.forClass(AuditLog.class);
        verify(auditLogRepository).save(captor.capture());

        AuditLog saved = captor.getValue();
        assertThat(saved.getPerformedById()).isEqualTo(userId);
        assertThat(saved.getAction()).isEqualTo("LOGIN_SUCCESS");
        assertThat(saved.getResourceType()).isEqualTo("USER");
        assertThat(saved.getResourceId()).isEqualTo(resourceId);
        assertThat(saved.getDetails()).isEqualTo("User logged in");
    }

    @Test
    void createAuditLog_withNullUserId_stillSaves() {
        // AuthServiceImpl logs failed logins for unknown emails with a
        // null performer id — this must not blow up.
        auditService.createAuditLog(null, "LOGIN_FAILURE", "AUTH", null, "Unknown email");

        ArgumentCaptor<AuditLog> captor = ArgumentCaptor.forClass(AuditLog.class);
        verify(auditLogRepository).save(captor.capture());
        assertThat(captor.getValue().getPerformedById()).isNull();
    }

    // --- getUserAuditLogs: tenant isolation ---

    @Test
    void getUserAuditLogs_sameHospital_succeeds() {
        authenticateAs(adminAtHospitalA, RoleType.HOSPITAL_ADMIN);
        when(userRepository.findByEmail(adminAtHospitalA.getEmail()))
                .thenReturn(Optional.of(adminAtHospitalA));
        when(userRepository.findById(targetAtHospitalA.getId()))
                .thenReturn(Optional.of(targetAtHospitalA));
        List<AuditLog> logs = List.of(AuditLog.builder().action("LOGIN_SUCCESS").build());
        when(auditLogRepository.findByPerformedById(targetAtHospitalA.getId())).thenReturn(logs);

        assertThat(auditService.getUserAuditLogs(targetAtHospitalA.getId())).isEqualTo(logs);
    }

    @Test
    void getUserAuditLogs_differentHospital_isDenied() {
        authenticateAs(adminAtHospitalA, RoleType.HOSPITAL_ADMIN);
        when(userRepository.findByEmail(adminAtHospitalA.getEmail()))
                .thenReturn(Optional.of(adminAtHospitalA));
        when(userRepository.findById(targetAtHospitalB.getId()))
                .thenReturn(Optional.of(targetAtHospitalB));

        assertThatThrownBy(() -> auditService.getUserAuditLogs(targetAtHospitalB.getId()))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void getUserAuditLogs_asSystemAdmin_bypassesTenantBoundary() {
        User sysAdmin = User.builder().id(UUID.randomUUID()).email("root@medmatch.org").build();
        authenticateAs(sysAdmin, RoleType.SYSTEM_ADMIN);
        List<AuditLog> logs = List.of(AuditLog.builder().action("LOGIN_SUCCESS").build());
        when(auditLogRepository.findByPerformedById(targetAtHospitalB.getId())).thenReturn(logs);

        assertThat(auditService.getUserAuditLogs(targetAtHospitalB.getId())).isEqualTo(logs);
    }

    @Test
    void getUserAuditLogs_targetUserNoLongerExists_isDeniedForNonAdmin() {
        authenticateAs(adminAtHospitalA, RoleType.HOSPITAL_ADMIN);
        when(userRepository.findByEmail(adminAtHospitalA.getEmail()))
                .thenReturn(Optional.of(adminAtHospitalA));
        UUID deletedUserId = UUID.randomUUID();
        when(userRepository.findById(deletedUserId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> auditService.getUserAuditLogs(deletedUserId))
                .isInstanceOf(AccessDeniedException.class);
    }
}
