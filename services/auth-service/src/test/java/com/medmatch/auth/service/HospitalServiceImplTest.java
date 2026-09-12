package com.medmatch.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.RoleType;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.DuplicateResourceException;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.HospitalRepository;
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

@ExtendWith(MockitoExtension.class)
class HospitalServiceImplTest {

    @Mock private HospitalRepository hospitalRepository;
    @Mock private UserRepository userRepository;

    @InjectMocks
    private HospitalServiceImpl hospitalService;

    private Hospital hospitalA;
    private Hospital hospitalB;
    private User adminAtHospitalA;

    @BeforeEach
    void setUp() {
        hospitalA = Hospital.builder().id(UUID.randomUUID()).code("HOSP_A").name("Hospital A").build();
        hospitalB = Hospital.builder().id(UUID.randomUUID()).code("HOSP_B").name("Hospital B").build();

        Role hospitalAdminRole = Role.builder().id(UUID.randomUUID()).name(RoleType.HOSPITAL_ADMIN).build();
        adminAtHospitalA = User.builder()
                .id(UUID.randomUUID()).email("admin@hospa.org")
                .role(hospitalAdminRole).hospital(hospitalA).build();
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

    // --- getHospitalById: tenant isolation ---

    @Test
    void getHospitalById_ownHospital_succeeds() {
        authenticateAs(adminAtHospitalA, RoleType.HOSPITAL_ADMIN);
        when(hospitalRepository.findById(hospitalA.getId())).thenReturn(Optional.of(hospitalA));
        when(userRepository.findByEmail(adminAtHospitalA.getEmail()))
                .thenReturn(Optional.of(adminAtHospitalA));

        assertThat(hospitalService.getHospitalById(hospitalA.getId()).getCode()).isEqualTo("HOSP_A");
    }

    @Test
    void getHospitalById_differentHospital_isDenied() {
        authenticateAs(adminAtHospitalA, RoleType.HOSPITAL_ADMIN);
        when(hospitalRepository.findById(hospitalB.getId())).thenReturn(Optional.of(hospitalB));
        when(userRepository.findByEmail(adminAtHospitalA.getEmail()))
                .thenReturn(Optional.of(adminAtHospitalA));

        assertThatThrownBy(() -> hospitalService.getHospitalById(hospitalB.getId()))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void getHospitalById_asSystemAdmin_bypassesTenantBoundary() {
        User sysAdmin = User.builder().id(UUID.randomUUID()).email("root@medmatch.org").build();
        authenticateAs(sysAdmin, RoleType.SYSTEM_ADMIN);
        when(hospitalRepository.findById(hospitalB.getId())).thenReturn(Optional.of(hospitalB));

        assertThat(hospitalService.getHospitalById(hospitalB.getId()).getCode()).isEqualTo("HOSP_B");
        verify(userRepository, never()).findByEmail(any());
    }

    @Test
    void getHospitalById_unknownId_throwsResourceNotFound() {
        UUID unknownId = UUID.randomUUID();
        when(hospitalRepository.findById(unknownId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> hospitalService.getHospitalById(unknownId))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    // --- createHospital ---

    @Test
    void createHospital_duplicateCode_throwsDuplicateResource() {
        Hospital newHospital = Hospital.builder().code("HOSP_A").name("Duplicate").build();
        when(hospitalRepository.existsByCode("HOSP_A")).thenReturn(true);

        assertThatThrownBy(() -> hospitalService.createHospital(newHospital))
                .isInstanceOf(DuplicateResourceException.class);

        verify(hospitalRepository, never()).save(any());
    }

    @Test
    void createHospital_newCode_persistsAndReturnsIt() {
        Hospital newHospital = Hospital.builder().code("HOSP_C").name("Hospital C").build();
        when(hospitalRepository.existsByCode("HOSP_C")).thenReturn(false);
        when(hospitalRepository.save(newHospital)).thenReturn(newHospital);

        assertThat(hospitalService.createHospital(newHospital).getCode()).isEqualTo("HOSP_C");
    }

    // --- updateHospital: inherits getHospitalById's tenant check ---

    @Test
    void updateHospital_differentHospital_isDenied_andNeverSaves() {
        authenticateAs(adminAtHospitalA, RoleType.HOSPITAL_ADMIN);
        when(hospitalRepository.findById(hospitalB.getId())).thenReturn(Optional.of(hospitalB));
        when(userRepository.findByEmail(adminAtHospitalA.getEmail()))
                .thenReturn(Optional.of(adminAtHospitalA));

        Hospital patch = Hospital.builder().name("Hijacked Name").build();

        assertThatThrownBy(() -> hospitalService.updateHospital(hospitalB.getId(), patch))
                .isInstanceOf(AccessDeniedException.class);

        verify(hospitalRepository, never()).save(any());
    }

    @Test
    void updateHospital_ownHospital_updatesNameAndAddress() {
        authenticateAs(adminAtHospitalA, RoleType.HOSPITAL_ADMIN);
        when(hospitalRepository.findById(hospitalA.getId())).thenReturn(Optional.of(hospitalA));
        when(userRepository.findByEmail(adminAtHospitalA.getEmail()))
                .thenReturn(Optional.of(adminAtHospitalA));
        when(hospitalRepository.save(any(Hospital.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        Hospital patch = Hospital.builder().name("Renamed Hospital A").address("123 New Address").build();

        Hospital updated = hospitalService.updateHospital(hospitalA.getId(), patch);

        assertThat(updated.getName()).isEqualTo("Renamed Hospital A");
        assertThat(updated.getAddress()).isEqualTo("123 New Address");
    }

    // --- deactivateHospital: SYSTEM_ADMIN only at the controller, bypasses the check ---

    @Test
    void deactivateHospital_asSystemAdmin_setsInactiveAndSaves() {
        User sysAdmin = User.builder().id(UUID.randomUUID()).email("root@medmatch.org").build();
        authenticateAs(sysAdmin, RoleType.SYSTEM_ADMIN);
        when(hospitalRepository.findById(hospitalA.getId())).thenReturn(Optional.of(hospitalA));
        when(hospitalRepository.save(any(Hospital.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        hospitalService.deactivateHospital(hospitalA.getId());

        assertThat(hospitalA.getActive()).isFalse();
        verify(hospitalRepository).save(hospitalA);
    }

    // --- misc ---

    @Test
    void getAllHospitals_returnsRepositoryResult() {
        when(hospitalRepository.findAll()).thenReturn(List.of(hospitalA, hospitalB));

        assertThat(hospitalService.getAllHospitals()).containsExactly(hospitalA, hospitalB);
    }

    @Test
    void getActiveHospitals_returnsOnlyActiveOnes() {
        when(hospitalRepository.findByActiveTrue()).thenReturn(List.of(hospitalA));

        assertThat(hospitalService.getActiveHospitals()).containsExactly(hospitalA);
    }

    @Test
    void existsByCode_delegatesToRepository() {
        when(hospitalRepository.existsByCode("HOSP_A")).thenReturn(true);

        assertThat(hospitalService.existsByCode("HOSP_A")).isTrue();
    }
}
