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
public class SystemMetricCard {


    /*
     * Main value shown in dashboard card
     *
     * Examples:
     * Total Users -> 2458
     * Active Hospitals -> 124
     */
    private String title;


    /*
     * Actual metric value
     */
    private Long value;


    /*
     * Growth percentage
     *
     * Example:
     * +8.7%
     */
    private Double growthPercentage;


    /*
     * Comparison text
     *
     * Example:
     * "vs last month"
     */
    private String comparison;


    /*
     * Icon identifier for frontend
     *
     * Examples:
     * USERS
     * HOSPITAL
     * TRIAL
     * MATCH
     */
    private String icon;
}