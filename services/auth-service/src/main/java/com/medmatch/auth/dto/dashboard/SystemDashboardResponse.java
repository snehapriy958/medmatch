package com.medmatch.auth.dto.dashboard;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


import java.util.List;



@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SystemDashboardResponse {


    /*
     * Top metric cards
     *
     * Examples:
     * Total Users
     * Active Hospitals
     * Active Trials
     * Matches Generated
     */
    private List<SystemMetricCard> metrics;



    /*
     * Top performing hospitals
     *
     * Used for:
     * Active Hospitals table
     */
    private List<HospitalSummaryResponse> topHospitals;



    /*
     * Audit overview
     *
     * Used for:
     * Compliance dashboard section
     */
    private AuditSummaryResponse auditSummary;



    /*
     * Platform health
     *
     * Used for:
     * System Health section
     */
    private SystemHealthResponse systemHealth;


}