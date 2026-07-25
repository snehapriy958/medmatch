package com.medmatch.auth.dto;

public class DashboardSummaryResponse {

    private long hospitalCount;
    private long userCount;

    public DashboardSummaryResponse() {
    }

    public DashboardSummaryResponse(long hospitalCount, long userCount) {
        this.hospitalCount = hospitalCount;
        this.userCount = userCount;
    }

    public long getHospitalCount() {
        return hospitalCount;
    }

    public void setHospitalCount(long hospitalCount) {
        this.hospitalCount = hospitalCount;
    }

    public long getUserCount() {
        return userCount;
    }

    public void setUserCount(long userCount) {
        this.userCount = userCount;
    }
}