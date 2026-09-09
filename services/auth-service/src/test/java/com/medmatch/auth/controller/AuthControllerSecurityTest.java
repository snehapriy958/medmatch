package com.medmatch.auth.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medmatch.auth.dto.AuthResponse;
import com.medmatch.auth.dto.LoginRequest;
import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;
import com.medmatch.auth.entity.RoleType;
import com.medmatch.auth.security.CustomUserDetailsService;
import com.medmatch.auth.security.JwtService;
import com.medmatch.auth.security.SecurityConfig;
import com.medmatch.auth.service.AuthService;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Verifies the two independent layers guarding /auth/register agree with
 * each other: SecurityConfig's requestMatcher-level hasAnyRole check and
 * AuthController's @PreAuthorize. Requests carry no Authorization header,
 * so JwtAuthenticationFilter (a real bean here) takes its no-op
 * pass-through path and the SecurityContext set up by
 * SecurityMockMvcRequestPostProcessors#user(...) is what's actually
 * evaluated.
 */
@WebMvcTest(AuthController.class)
@Import(SecurityConfig.class)
class AuthControllerSecurityTest {

    @Autowired private MockMvc mockMvc;
    
    private final ObjectMapper objectMapper = new ObjectMapper();

    @MockitoBean private AuthService authService;
    @MockitoBean private JwtService jwtService;
    @MockitoBean private CustomUserDetailsService customUserDetailsService;
    @MockitoBean private PasswordEncoder passwordEncoder;

    @Test
    void login_isReachableWithoutAuthentication() throws Exception {
        LoginRequest request = LoginRequest.builder()
                .email("dr.priya@testhosp.org")
                .password("correct-password")
                .build();
        when(authService.login(any())).thenReturn(
                AuthResponse.builder().accessToken("token").expiresIn(3600000L).build());

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk());
    }

    @Test
    void register_withNoAuthentication_isRejected() throws Exception {
        // Filter-chain-level check (SecurityConfig.authorizeHttpRequests)
        // runs before DispatcherServlet, so an empty/invalid body is fine
        // here — the request never reaches the controller.
        mockMvc.perform(post("/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().is4xxClientError());
    }

    @Test
    void register_authenticatedAsPhysician_isForbidden() throws Exception {
        mockMvc.perform(post("/auth/register")
                        .with(user("physician@testhosp.org").roles("PHYSICIAN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void register_authenticatedAsHospitalAdmin_isAllowedThrough() throws Exception {
        RegisterRequest request = RegisterRequest.builder()
                .firstName("New").lastName("Physician")
                .email("new.physician@testhosp.org")
                .password("StrongPassword123")
                .hospitalId(UUID.randomUUID())
                .role(RoleType.PHYSICIAN)
                .build();
        when(authService.register(any())).thenReturn(
                UserResponse.builder().email(request.getEmail()).role(RoleType.PHYSICIAN).build());

        mockMvc.perform(post("/auth/register")
                        .with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated());
    }

    @Test
    void register_authenticatedAsSystemAdmin_isAllowedThrough() throws Exception {
        RegisterRequest request = RegisterRequest.builder()
                .firstName("New").lastName("Admin")
                .email("new.admin@testhosp.org")
                .password("StrongPassword123")
                .hospitalId(UUID.randomUUID())
                .role(RoleType.HOSPITAL_ADMIN)
                .build();
        when(authService.register(any())).thenReturn(
                UserResponse.builder().email(request.getEmail()).role(RoleType.HOSPITAL_ADMIN).build());

        mockMvc.perform(post("/auth/register")
                        .with(user("root@medmatch.org").roles("SYSTEM_ADMIN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated());
    }
}
