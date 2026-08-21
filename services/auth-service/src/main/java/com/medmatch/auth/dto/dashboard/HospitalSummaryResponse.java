package com.medmatch.auth.dto.dashboard;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;


@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HospitalSummaryResponse {


    /*
     * Hospital identifier
     */
    private UUID hospitalId;


    /*
     * Hospital display name
     *
     * Example:
     * City Hospital, NY
     */
    private String hospitalName;


    /*
     * Total users belonging to hospital
     */
    private Long totalUsers;


    /*
     * Total patients in hospital
     *
     * Used for:
     * Top Active Hospitals table
     */
    private Long totalPatients;


    /*
     * Active clinical trials
     */
    private Long activeTrials;


    /*
     * Generated matches count
     */
    private Long matchesGenerated;
}