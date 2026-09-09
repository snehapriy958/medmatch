package com.medmatch.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.medmatch.auth.dto.AuthResponse;
import com.medmatch.auth.dto.LoginRequest;
import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;
import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.RoleType;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.EmailAlreadyExistsException;
import com.medmatch.auth.exception.InvalidCredentialsException;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.RoleRepository;
import com.medmatch.auth.repository.UserRepository;
import com.medmatch.auth.security.JwtService;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthServiceImplTest {

    @Mock private UserRepository userRepository;
    @Mock private RoleRepository roleRepository;
    @Mock private HospitalRepository hospitalRepository;
    @Mock private AuditService auditService;
    @Mock private PasswordEncoder passwordEncoder;
    @Mock private JwtService jwtService;

    @InjectMocks
    private AuthServiceImpl authService;

    private Hospital activeHospital;
    private Role physicianRole;
    private User existingUser;

    @BeforeEach
    void setUp() {
        activeHospital = Hospital.builder()
                .id(UUID.randomUUID())
                .code("TESTHOSP")
                .name("Test Hospital")
                .active(true)
                .build();

        physicianRole = Role.builder()
                .id(UUID.randomUUID())
                .name(RoleType.PHYSICIAN)
                .build();

        existingUser = User.builder()
                .id(UUID.randomUUID())
                .email("dr.priya@testhosp.org")
                .password("bcrypt-hash")
                .firstName("Priya")
                .lastName("S")
                .role(physicianRole)
                .hospital(activeHospital)
                .enabled(true)
                .build();
    }

    // --- register() ---

    @Test
    void register_whenEmailAlreadyExists_throwsAndNeverTouchesHospitalOrRole() {
        RegisterRequest request = validRegisterRequest();
        when(userRepository.existsByEmail(request.getEmail())).thenReturn(true);

        assertThatThrownBy(() -> authService.register(request))
                .isInstanceOf(EmailAlreadyExistsException.class);

        verify(hospitalRepository, never()).findById(any());
        verify(userRepository, never()).save(any());
    }

    @Test
    void register_whenHospitalNotFound_throwsResourceNotFound() {
        RegisterRequest request = validRegisterRequest();
        when(userRepository.existsByEmail(request.getEmail())).thenReturn(false);
        when(hospitalRepository.findById(request.getHospitalId())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.register(request))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("Hospital");
    }

    @Test
    void register_whenHospitalInactive_throwsResourceNotFound() {
        activeHospital.setActive(false);
        RegisterRequest request = validRegisterRequest();
        when(userRepository.existsByEmail(request.getEmail())).thenReturn(false);
        when(hospitalRepository.findById(request.getHospitalId()))
                .thenReturn(Optional.of(activeHospital));

        assertThatThrownBy(() -> authService.register(request))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("inactive");

        verify(roleRepository, never()).findByName(any());
    }

    @Test
    void register_whenRoleNotFound_throwsResourceNotFound() {
        RegisterRequest request = validRegisterRequest();
        when(userRepository.existsByEmail(request.getEmail())).thenReturn(false);
        when(hospitalRepository.findById(request.getHospitalId()))
                .thenReturn(Optional.of(activeHospital));
        when(roleRepository.findByName(request.getRole())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.register(request))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("Role");
    }

    @Test
    void register_success_hashesPasswordAndPersistsEnabledUser() {
        RegisterRequest request = validRegisterRequest();
        when(userRepository.existsByEmail(request.getEmail())).thenReturn(false);
        when(hospitalRepository.findById(request.getHospitalId()))
                .thenReturn(Optional.of(activeHospital));
        when(roleRepository.findByName(request.getRole())).thenReturn(Optional.of(physicianRole));
        when(passwordEncoder.encode(request.getPassword())).thenReturn("bcrypt-hash");
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> {
            User u = invocation.getArgument(0);
            u.setId(UUID.randomUUID());
            return u;
        });

        UserResponse response = authService.register(request);

        ArgumentCaptor<User> savedUser = ArgumentCaptor.forClass(User.class);
        verify(userRepository).save(savedUser.capture());

        // The critical assertion: the plaintext password never reaches
        // the repository — only the encoder's output does.
        assertThat(savedUser.getValue().getPassword()).isEqualTo("bcrypt-hash");
        assertThat(savedUser.getValue().getPassword()).isNotEqualTo(request.getPassword());
        assertThat(savedUser.getValue().getEnabled()).isTrue();
        assertThat(response.getEmail()).isEqualTo(request.getEmail());
        assertThat(response.getRole()).isEqualTo(RoleType.PHYSICIAN);
    }

    // --- login() ---

    @Test
    void login_whenUserNotFound_throwsInvalidCredentials() {
        LoginRequest request = new LoginRequest();
        request.setEmail("nobody@testhosp.org");
        request.setPassword("whatever123");
        when(userRepository.findByEmail(request.getEmail())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(InvalidCredentialsException.class);

        verify(jwtService, never()).generateToken(any());
    }

    @Test
    void login_whenPasswordWrong_throwsInvalidCredentials_andNeverIssuesToken() {
        LoginRequest request = new LoginRequest();
        request.setEmail(existingUser.getEmail());
        request.setPassword("wrong-password");
        when(userRepository.findByEmail(request.getEmail())).thenReturn(Optional.of(existingUser));
        when(passwordEncoder.matches(request.getPassword(), existingUser.getPassword()))
                .thenReturn(false);

        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(InvalidCredentialsException.class);

        verify(jwtService, never()).generateToken(any());
    }

    @Test
    void login_whenUserDisabled_throwsInvalidCredentials_evenWithCorrectPassword() {
        existingUser.setEnabled(false);
        LoginRequest request = new LoginRequest();
        request.setEmail(existingUser.getEmail());
        request.setPassword("correct-password");
        when(userRepository.findByEmail(request.getEmail())).thenReturn(Optional.of(existingUser));
        when(passwordEncoder.matches(request.getPassword(), existingUser.getPassword()))
                .thenReturn(true);

        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(InvalidCredentialsException.class)
                .hasMessageContaining("disabled");

        verify(jwtService, never()).generateToken(any());
    }

    @Test
    void login_success_returnsTokenAndAuditsTheLogin() {
        LoginRequest request = new LoginRequest();
        request.setEmail(existingUser.getEmail());
        request.setPassword("correct-password");
        when(userRepository.findByEmail(request.getEmail())).thenReturn(Optional.of(existingUser));
        when(passwordEncoder.matches(request.getPassword(), existingUser.getPassword()))
                .thenReturn(true);
        when(jwtService.generateToken(existingUser)).thenReturn("signed.jwt.token");

        AuthResponse response = authService.login(request);

        assertThat(response.getAccessToken()).isEqualTo("signed.jwt.token");
        assertThat(response.getUser().getEmail()).isEqualTo(existingUser.getEmail());
        verify(auditService).createAuditLog(
                existingUser.getId(), "LOGIN_SUCCESS", "USER", existingUser.getId(),
                "User logged in: " + existingUser.getEmail());
    }

    private RegisterRequest validRegisterRequest() {
        return RegisterRequest.builder()
                .firstName("New")
                .lastName("Coordinator")
                .email("new.coordinator@testhosp.org")
                .password("StrongPassword123")
                .hospitalId(activeHospital.getId())
                .role(RoleType.PHYSICIAN)
                .build();
    }
}
