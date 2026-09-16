package com.medmatch.auth.controller;

import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.medmatch.auth.security.CustomUserDetailsService;
import com.medmatch.auth.security.JwtService;
import com.medmatch.auth.security.SecurityConfig;
import com.medmatch.auth.service.AuditService;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(AuditController.class)
@Import(SecurityConfig.class)
class AuditControllerTest {

    @Autowired private MockMvc mockMvc;

    @MockitoBean private AuditService auditService;
    @MockitoBean private JwtService jwtService;
    @MockitoBean private CustomUserDetailsService customUserDetailsService;
    @MockitoBean private PasswordEncoder passwordEncoder;

    @Test
    void getUserAuditLogs_withoutAuthentication_isRejected() throws Exception {
        mockMvc.perform(get("/audit-logs/user/" + UUID.randomUUID()))
                .andExpect(status().is4xxClientError());
    }

    @Test
    void getUserAuditLogs_asPhysician_isForbidden() throws Exception {
        mockMvc.perform(get("/audit-logs/user/" + UUID.randomUUID())
                        .with(user("physician@testhosp.org").roles("PHYSICIAN")))
                .andExpect(status().isForbidden());
    }

    @Test
    void getUserAuditLogs_asHospitalAdmin_isAllowed() throws Exception {
        UUID targetId = UUID.randomUUID();
        when(auditService.getUserAuditLogs(targetId)).thenReturn(List.of());

        mockMvc.perform(get("/audit-logs/user/" + targetId)
                        .with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN")))
                .andExpect(status().isOk());
    }

    @Test
    void getUserAuditLogs_asSystemAdmin_isAllowed() throws Exception {
        UUID targetId = UUID.randomUUID();
        when(auditService.getUserAuditLogs(targetId)).thenReturn(List.of());

        mockMvc.perform(get("/audit-logs/user/" + targetId)
                        .with(user("root@medmatch.org").roles("SYSTEM_ADMIN")))
                .andExpect(status().isOk());
    }
}
