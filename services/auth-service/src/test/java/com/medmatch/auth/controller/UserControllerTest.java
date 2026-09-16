package com.medmatch.auth.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;
import com.medmatch.auth.entity.RoleType;
import com.medmatch.auth.security.CustomUserDetailsService;
import com.medmatch.auth.security.JwtService;
import com.medmatch.auth.security.SecurityConfig;
import com.medmatch.auth.service.UserService;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(UserController.class)
@Import(SecurityConfig.class)
class UserControllerTest {

    @Autowired private MockMvc mockMvc;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @MockitoBean private UserService userService;
    @MockitoBean private JwtService jwtService;
    @MockitoBean private CustomUserDetailsService customUserDetailsService;
    @MockitoBean private PasswordEncoder passwordEncoder;

    // --- GET /users/me: isAuthenticated() only, any role ---

    @Test
    void getCurrentUser_withoutAuthentication_isRejected() throws Exception {
        mockMvc.perform(get("/users/me"))
                .andExpect(status().is4xxClientError());
    }

    @Test
    void getCurrentUser_asPhysician_isAllowed() throws Exception {
        when(userService.getUserByEmail("physician@testhosp.org")).thenReturn(
                UserResponse.builder().email("physician@testhosp.org").role(RoleType.PHYSICIAN).build());

        mockMvc.perform(get("/users/me").with(user("physician@testhosp.org").roles("PHYSICIAN")))
                .andExpect(status().isOk());
    }

    // --- POST /users: SYSTEM_ADMIN or HOSPITAL_ADMIN only ---

        @Test
        void createUser_asPhysician_isForbidden() throws Exception {
        RegisterRequest request = RegisterRequest.builder()
                .firstName("Test")
                .lastName("Physician")
                .email("physician.create@testhosp.org")
                .password("StrongPassword123")
                .hospitalId(UUID.randomUUID())
                .role(RoleType.PHYSICIAN)
                .build();

        mockMvc.perform(post("/users")
                        .with(user("physician@testhosp.org").roles("PHYSICIAN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isForbidden());
        }

    @Test
    void createUser_asHospitalAdmin_isAllowed() throws Exception {
        RegisterRequest request = RegisterRequest.builder()
                .firstName("New").lastName("Nurse")
                .email("new.nurse@testhosp.org").password("StrongPassword123")
                .hospitalId(UUID.randomUUID()).role(RoleType.PHYSICIAN)
                .build();
        when(userService.createUser(any())).thenReturn(
                UserResponse.builder().email(request.getEmail()).role(RoleType.PHYSICIAN).build());

        mockMvc.perform(post("/users")
                        .with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated());
    }

    // --- GET /users/{id}: SYSTEM_ADMIN or HOSPITAL_ADMIN only ---

    @Test
    void getUserById_asPhysician_isForbidden() throws Exception {
        mockMvc.perform(get("/users/" + UUID.randomUUID())
                        .with(user("physician@testhosp.org").roles("PHYSICIAN")))
                .andExpect(status().isForbidden());
    }

    @Test
    void getUserById_asHospitalAdmin_isAllowed() throws Exception {
        UUID id = UUID.randomUUID();
        when(userService.getUserById(id)).thenReturn(
                UserResponse.builder().id(id).email("x@testhosp.org").role(RoleType.PHYSICIAN).build());

        mockMvc.perform(get("/users/" + id).with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN")))
                .andExpect(status().isOk());
    }

    // --- GET /users/hospital/{hospitalId} ---

    @Test
    void getUsersByHospital_asPhysician_isForbidden() throws Exception {
        mockMvc.perform(get("/users/hospital/" + UUID.randomUUID())
                        .with(user("physician@testhosp.org").roles("PHYSICIAN")))
                .andExpect(status().isForbidden());
    }

    @Test
    void getUsersByHospital_asSystemAdmin_isAllowed() throws Exception {
        UUID hospitalId = UUID.randomUUID();
        when(userService.getUsersByHospital(hospitalId)).thenReturn(List.of());

        mockMvc.perform(get("/users/hospital/" + hospitalId)
                        .with(user("root@medmatch.org").roles("SYSTEM_ADMIN")))
                .andExpect(status().isOk());
    }

    // --- DELETE /users/{id} ---

    @Test
    void deleteUser_asPhysician_isForbidden() throws Exception {
        mockMvc.perform(delete("/users/" + UUID.randomUUID())
                        .with(user("physician@testhosp.org").roles("PHYSICIAN")))
                .andExpect(status().isForbidden());
    }

    @Test
    void deleteUser_asHospitalAdmin_isAllowed() throws Exception {
        UUID id = UUID.randomUUID();

        mockMvc.perform(delete("/users/" + id).with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN")))
                .andExpect(status().isNoContent());
    }
}
