package com.medmatch.auth.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuditSummaryResponse {


    /*
     * Total audit events
     *
     * Dashboard:
     * Audit Log Summary
     */
    private Long totalEvents;



    /*
     * User activities
     *
     * Examples:
     * LOGIN_SUCCESS
     * USER_REGISTERED
     * PROFILE_UPDATED
     */
    private Long userActivities;



    /*
     * Data access events
     *
     * Examples:
     * PATIENT_VIEWED
     * TRIAL_ACCESSED
     */
    private Long dataAccess;



    /*
     * Configuration changes
     *
     * Examples:
     * ROLE_UPDATED
     * SETTINGS_CHANGED
     */
    private Long configurationChanges;



    /*
     * Security related events
     *
     * Examples:
     * FAILED_LOGIN
     * UNAUTHORIZED_ACCESS
     */
    private Long securityEvents;
}