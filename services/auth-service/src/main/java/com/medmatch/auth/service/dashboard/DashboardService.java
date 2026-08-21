package com.medmatch.auth.service.dashboard;


import com.medmatch.auth.dto.dashboard.SystemDashboardResponse;



public interface DashboardService {


    /*
     * System Administrator Dashboard
     *
     * Provides:
     * - Platform metrics
     * - Hospital summary
     * - Audit summary
     * - System health
     */
    SystemDashboardResponse getSystemDashboard();

}