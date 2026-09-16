package com.medmatch.auth.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.security.CustomUserDetailsService;
import com.medmatch.auth.security.JwtService;
import com.medmatch.auth.security.SecurityConfig;
import com.medmatch.auth.service.HospitalService;
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

@WebMvcTest(HospitalController.class)
@Import(SecurityConfig.class)
class HospitalControllerTest {

    @Autowired private MockMvc mockMvc;

    @MockitoBean private HospitalService hospitalService;
    @MockitoBean private JwtService jwtService;
    @MockitoBean private CustomUserDetailsService customUserDetailsService;
    @MockitoBean private PasswordEncoder passwordEncoder;

    // --- POST /hospitals: SYSTEM_ADMIN only ---

    @Test
    void createHospital_asHospitalAdmin_isForbidden() throws Exception {
        mockMvc.perform(post("/hospitals")
                        .with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void createHospital_asSystemAdmin_isAllowed() throws Exception {
        when(hospitalService.createHospital(any())).thenReturn(
                Hospital.builder().id(UUID.randomUUID()).code("NEWHOSP").name("New Hospital").build());

        mockMvc.perform(post("/hospitals")
                        .with(user("root@medmatch.org").roles("SYSTEM_ADMIN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"code\":\"NEWHOSP\",\"name\":\"New Hospital\"}"))
                .andExpect(status().isCreated());
    }

    // --- GET /hospitals/{id}: SYSTEM_ADMIN or HOSPITAL_ADMIN ---

    @Test
    void getHospitalById_asPhysician_isForbidden() throws Exception {
        mockMvc.perform(get("/hospitals/" + UUID.randomUUID())
                        .with(user("physician@testhosp.org").roles("PHYSICIAN")))
                .andExpect(status().isForbidden());
    }

    @Test
    void getHospitalById_asHospitalAdmin_isAllowed() throws Exception {
        UUID id = UUID.randomUUID();
        when(hospitalService.getHospitalById(id)).thenReturn(
                Hospital.builder().id(id).code("HOSP_A").name("Hospital A").build());

        mockMvc.perform(get("/hospitals/" + id).with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN")))
                .andExpect(status().isOk());
    }

    // --- GET /hospitals: SYSTEM_ADMIN only ---

    @Test
    void getAllHospitals_asHospitalAdmin_isForbidden() throws Exception {
        mockMvc.perform(get("/hospitals").with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN")))
                .andExpect(status().isForbidden());
    }

    @Test
    void getAllHospitals_asSystemAdmin_isAllowed() throws Exception {
        when(hospitalService.getAllHospitals()).thenReturn(List.of());

        mockMvc.perform(get("/hospitals").with(user("root@medmatch.org").roles("SYSTEM_ADMIN")))
                .andExpect(status().isOk());
    }

    // --- GET /hospitals/active: SYSTEM_ADMIN only ---

    @Test
    void getActiveHospitals_asHospitalAdmin_isForbidden() throws Exception {
        mockMvc.perform(get("/hospitals/active").with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN")))
                .andExpect(status().isForbidden());
    }

    // --- PUT /hospitals/{id}: SYSTEM_ADMIN or HOSPITAL_ADMIN ---

    @Test
    void updateHospital_asPhysician_isForbidden() throws Exception {
        mockMvc.perform(put("/hospitals/" + UUID.randomUUID())
                        .with(user("physician@testhosp.org").roles("PHYSICIAN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void updateHospital_asHospitalAdmin_isAllowed() throws Exception {
        UUID id = UUID.randomUUID();
        when(hospitalService.updateHospital(any(), any())).thenReturn(
                Hospital.builder().id(id).code("HOSP_A").name("Renamed").build());

        mockMvc.perform(put("/hospitals/" + id)
                        .with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Renamed\"}"))
                .andExpect(status().isOk());
    }

    // --- DELETE /hospitals/{id}: SYSTEM_ADMIN only ---

    @Test
    void deactivateHospital_asHospitalAdmin_isForbidden() throws Exception {
        mockMvc.perform(delete("/hospitals/" + UUID.randomUUID())
                        .with(user("admin@testhosp.org").roles("HOSPITAL_ADMIN")))
                .andExpect(status().isForbidden());
    }

    @Test
    void deactivateHospital_asSystemAdmin_isAllowed() throws Exception {
        UUID id = UUID.randomUUID();

        mockMvc.perform(delete("/hospitals/" + id).with(user("root@medmatch.org").roles("SYSTEM_ADMIN")))
                .andExpect(status().isNoContent());
    }
}
