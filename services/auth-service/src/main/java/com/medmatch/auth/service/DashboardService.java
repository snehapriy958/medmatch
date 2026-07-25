package com.medmatch.auth.service;

import org.springframework.stereotype.Service;

import com.medmatch.auth.dto.DashboardSummaryResponse;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.UserRepository;

@Service
public class DashboardService {

    private final HospitalRepository hospitalRepository;
    private final UserRepository userRepository;

    public DashboardService(
            HospitalRepository hospitalRepository,
            UserRepository userRepository
    ) {
        this.hospitalRepository = hospitalRepository;
        this.userRepository = userRepository;
    }

    public DashboardSummaryResponse getSummary() {

        long hospitalCount = hospitalRepository.count();
        long userCount = userRepository.count();

        return new DashboardSummaryResponse(
                hospitalCount,
                userCount
        );
    }
}