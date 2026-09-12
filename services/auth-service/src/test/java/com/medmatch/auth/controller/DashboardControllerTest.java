package com.medmatch.auth.controller;

import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.medmatch.auth.dto.dashboard.SystemDashboardResponse;
import com.medmatch.auth.security.CustomUserDetailsService;
import com.medmatch.auth.security.JwtService;
import com.medmatch.auth.security.SecurityConfig;
import com.medmatch.auth.service.dashboard.DashboardService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(DashboardController.class)
@Import(SecurityConfig.class)
class DashboardControllerTest {

    @Autowired private MockMvc mockMvc;

    @MockitoBean private DashboardService dashboardService;
    @MockitoBean private JwtService jwtService;
    @MockitoBean private CustomUserDetailsService customUserDetailsService;
    @MockitoBean private PasswordEncoder passwordEncoder;

    @Test
    void getSystemDashboard_withoutAuthentication_isRejected() throws Exception {
        mockMvc.perform(get("/dashboard/system"))
                .andExpect(status().is4xxClientError());
    }

    @Test
    void getSystemDashboard_asHospitalAdmin_isForbidden() throws Exception {
        // System dashboard is platform-wide (all hospitals) — HOSPITAL_ADMIN
        // must not see it, unlike the per-hospital endpoints elsewhere.
        mockMvc.perform(get("/dashboard/system")
                        .with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN")))
                .andExpect(status().isForbidden());
    }

    @Test
    void getSystemDashboard_asSystemAdmin_isAllowed() throws Exception {
        when(dashboardService.getSystemDashboard()).thenReturn(SystemDashboardResponse.builder().build());

        mockMvc.perform(get("/dashboard/system").with(user("root@medmatch.org").roles("SYSTEM_ADMIN")))
                .andExpect(status().isOk());
    }
}
