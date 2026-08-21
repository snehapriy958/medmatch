package com.medmatch.auth.controller;


import com.medmatch.auth.dto.dashboard.SystemDashboardResponse;
import com.medmatch.auth.service.dashboard.DashboardService;


import lombok.RequiredArgsConstructor;


import org.springframework.http.ResponseEntity;

import org.springframework.security.access.prepost.PreAuthorize;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;



@RestController
@RequestMapping("/dashboard")
@RequiredArgsConstructor
public class DashboardController {


    private final DashboardService dashboardService;



    /*
     * System Administrator Dashboard
     *
     * Access:
     * SYSTEM_ADMIN only
     *
     * Provides:
     * - Platform metrics
     * - Hospital statistics
     * - Audit summary
     * - System health
     */
    @GetMapping("/system")
    @PreAuthorize("hasRole('SYSTEM_ADMIN')")
    public ResponseEntity<SystemDashboardResponse> getSystemDashboard(){


        return ResponseEntity.ok(
                dashboardService.getSystemDashboard()
        );

    }

}