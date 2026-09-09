package com.medmatch.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.RoleType;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.RoleRepository;
import com.medmatch.auth.repository.UserRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;

/**
 * The tests in this class are the regression guard for the exact gap
 * flagged during the MedMatch build: a coordinator/physician at Hospital A
 * must never be able to read or delete a user record belonging to
 * Hospital B, regardless of what id they pass in the URL. SYSTEM_ADMIN is
 * the one role explicitly allowed to bypass the hospital boundary.
 */
@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {

    @Mock private UserRepository userRepository;
    @Mock private HospitalRepository hospitalRepository;
    @Mock private RoleRepository roleRepository;
    @Mock private PasswordEncoder passwordEncoder;

    @InjectMocks
    private UserServiceImpl userService;

    private Hospital hospitalA;
    private Hospital hospitalB;
    private User callerAtHospitalA;
    private User targetAtHospitalA;
    private User targetAtHospitalB;

    @BeforeEach
    void setUp() {
        hospitalA = Hospital.builder().id(UUID.randomUUID()).code("HOSP_A").name("Hospital A").build();
        hospitalB = Hospital.builder().id(UUID.randomUUID()).code("HOSP_B").name("Hospital B").build();

        Role physician = Role.builder().id(UUID.randomUUID()).name(RoleType.PHYSICIAN).build();

        callerAtHospitalA = User.builder()
                .id(UUID.randomUUID()).email("caller@hospa.org")
                .role(physician).hospital(hospitalA).build();

        targetAtHospitalA = User.builder()
                .id(UUID.randomUUID()).email("colleague@hospa.org")
                .firstName("Colleague").lastName("A").role(physician).hospital(hospitalA).build();

        targetAtHospitalB = User.builder()
                .id(UUID.randomUUID()).email("stranger@hospb.org")
                .firstName("Stranger").lastName("B").role(physician).hospital(hospitalB).build();
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

    // --- getUserById: hospital isolation ---

    @Test
    void getUserById_sameHospital_succeeds() {
        authenticateAs(callerAtHospitalA, RoleType.PHYSICIAN);
        when(userRepository.findById(targetAtHospitalA.getId()))
                .thenReturn(Optional.of(targetAtHospitalA));
        when(userRepository.findByEmail(callerAtHospitalA.getEmail()))
                .thenReturn(Optional.of(callerAtHospitalA));

        assertThat(userService.getUserById(targetAtHospitalA.getId()).getEmail())
                .isEqualTo(targetAtHospitalA.getEmail());
    }

    @Test
    void getUserById_differentHospital_isDenied() {
        authenticateAs(callerAtHospitalA, RoleType.PHYSICIAN);
        when(userRepository.findById(targetAtHospitalB.getId()))
                .thenReturn(Optional.of(targetAtHospitalB));
        when(userRepository.findByEmail(callerAtHospitalA.getEmail()))
                .thenReturn(Optional.of(callerAtHospitalA));

        assertThatThrownBy(() -> userService.getUserById(targetAtHospitalB.getId()))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void getUserById_asSystemAdmin_bypassesHospitalBoundary() {
        User admin = User.builder().id(UUID.randomUUID()).email("admin@medmatch.org").build();
        authenticateAs(admin, RoleType.SYSTEM_ADMIN);
        when(userRepository.findById(targetAtHospitalB.getId()))
                .thenReturn(Optional.of(targetAtHospitalB));

        assertThat(userService.getUserById(targetAtHospitalB.getId()).getEmail())
                .isEqualTo(targetAtHospitalB.getEmail());

        // Bypassing the check means the caller's own hospital never needs
        // to be looked up at all.
        verify(userRepository, never()).findByEmail("admin@medmatch.org");
    }

    @Test
    void getUserById_unknownId_throwsResourceNotFound_beforeAnyHospitalCheck() {
        authenticateAs(callerAtHospitalA, RoleType.PHYSICIAN);
        UUID unknownId = UUID.randomUUID();
        when(userRepository.findById(unknownId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> userService.getUserById(unknownId))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    // --- deleteUser: hospital isolation ---

    @Test
    void deleteUser_differentHospital_isDenied_andNeverDeletes() {
        authenticateAs(callerAtHospitalA, RoleType.PHYSICIAN);
        when(userRepository.findById(targetAtHospitalB.getId()))
                .thenReturn(Optional.of(targetAtHospitalB));
        when(userRepository.findByEmail(callerAtHospitalA.getEmail()))
                .thenReturn(Optional.of(callerAtHospitalA));

        assertThatThrownBy(() -> userService.deleteUser(targetAtHospitalB.getId()))
                .isInstanceOf(AccessDeniedException.class);

        verify(userRepository, never()).delete(targetAtHospitalB);
    }

    @Test
    void deleteUser_sameHospital_succeeds() {
        authenticateAs(callerAtHospitalA, RoleType.PHYSICIAN);
        when(userRepository.findById(targetAtHospitalA.getId()))
                .thenReturn(Optional.of(targetAtHospitalA));
        when(userRepository.findByEmail(callerAtHospitalA.getEmail()))
                .thenReturn(Optional.of(callerAtHospitalA));

        userService.deleteUser(targetAtHospitalA.getId());

        verify(userRepository).delete(targetAtHospitalA);
    }
}
