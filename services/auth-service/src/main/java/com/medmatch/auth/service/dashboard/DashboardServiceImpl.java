package com.medmatch.auth.service.dashboard;

import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;
import com.medmatch.auth.dto.dashboard.AuditSummaryResponse;
import com.medmatch.auth.dto.dashboard.HospitalSummaryResponse;
import com.medmatch.auth.dto.dashboard.SystemDashboardResponse;
import com.medmatch.auth.dto.dashboard.SystemHealthResponse;
import com.medmatch.auth.dto.dashboard.SystemMetricCard;
import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.repository.AuditLogRepository;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.UserRepository;

import lombok.RequiredArgsConstructor;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.List;
import java.util.UUID;


@Service
@RequiredArgsConstructor
public class DashboardServiceImpl implements DashboardService {

    private final UserRepository userRepository;

    private final HospitalRepository hospitalRepository;

    private final AuditLogRepository auditLogRepository;

    private final DataSource dataSource;

    private final ObjectMapper objectMapper;

    @Value("${AI_SERVICE_URL:http://ai-service:8000}")
    private String aiServiceUrl;


    @Override
    @Transactional(readOnly = true)
    public SystemDashboardResponse getSystemDashboard() {

        /*
         * Metric cards
         */
        List<SystemMetricCard> metrics = List.of(

                SystemMetricCard.builder()
                        .title("Total Users")
                        .value(
                                userRepository.count()
                        )
                        .growthPercentage(0.0)
                        .comparison("Current")
                        .icon("USERS")
                        .build(),

                SystemMetricCard.builder()
                        .title("Active Users")
                        .value(
                                userRepository.countByStatus("ACTIVE")
                        )
                        .growthPercentage(0.0)
                        .comparison("Current")
                        .icon("ACTIVE_USERS")
                        .build(),

                SystemMetricCard.builder()
                        .title("Active Hospitals")
                        .value(
                                (long) hospitalRepository
                                        .findByActiveTrue()
                                        .size()
                        )
                        .growthPercentage(0.0)
                        .comparison("Current")
                        .icon("HOSPITAL")
                        .build()
        );


        /*
         * Top hospitals
         */
        List<HospitalSummaryResponse> hospitals =
                hospitalRepository.findAll()
                        .stream()
                        .map(this::mapHospital)
                        .toList();


        /*
         * Audit summary
         */
        AuditSummaryResponse auditSummary =
                AuditSummaryResponse.builder()
                        .totalEvents(
                                auditLogRepository.count()
                        )
                        .userActivities(
                                auditLogRepository.countByAction(
                                        "LOGIN_SUCCESS"
                                )
                        )
                        .dataAccess(0L)
                        .configurationChanges(0L)
                        .securityEvents(0L)
                        .build();


        /*
         * System health
         */
        SystemHealthResponse health =
                getSystemHealth();


        return SystemDashboardResponse.builder()
                .metrics(metrics)
                .topHospitals(hospitals)
                .auditSummary(auditSummary)
                .systemHealth(health)
                .build();
    }


    /**
     * Build real-time system health information.
     *
     * Auth service checks PostgreSQL directly.
     * AI service readiness endpoint reports:
     * - database
     * - Redis
     * - pgvector/vector search
     * - uploads
     */
    private SystemHealthResponse getSystemHealth() {

        String authStatus = "UP";
        String databaseStatus = checkDatabase();

        String aiStatus = "DOWN";
        String redisStatus = "DOWN";
        String vectorSearchStatus = "DOWN";

        try {

            String healthUrl =
                    aiServiceUrl + "/api/health/ready";

            RestClient restClient =
                    RestClient.builder().build();

            ResponseEntity<String> response =
                    restClient
                            .get()
                            .uri(healthUrl)
                            .retrieve()
                            .toEntity(String.class);

            if (response.getStatusCode().is2xxSuccessful()
                    && response.getBody() != null) {

                JsonNode root =
                        objectMapper.readTree(
                                response.getBody()
                        );

                String overallAiStatus =
                        root.path("status")
                                .asText("DOWN");

                if ("UP".equalsIgnoreCase(
                        overallAiStatus
                )) {
                    aiStatus = "UP";
                }

                JsonNode checks =
                        root.path("checks");

                redisStatus =
                        normalizeStatus(
                                checks.path("redis")
                                        .asText("DOWN")
                        );

                vectorSearchStatus =
                        normalizeStatus(
                                checks.path("vector_search")
                                        .asText("DOWN")
                        );
            }

        } catch (Exception ignored) {

            /*
             * AI service unavailable.
             *
             * Keep the dashboard available rather than
             * allowing one dependency failure to break
             * the entire dashboard endpoint.
             */
            aiStatus = "DOWN";
            redisStatus = "DOWN";
            vectorSearchStatus = "DOWN";
        }


        String overallStatus =
                determineOverallStatus(
                        authStatus,
                        databaseStatus,
                        aiStatus,
                        redisStatus,
                        vectorSearchStatus
                );


        return SystemHealthResponse.builder()
                .authServiceStatus(authStatus)
                .databaseStatus(databaseStatus)
                .aiServiceStatus(aiStatus)
                .redisStatus(redisStatus)
                .vectorSearchStatus(vectorSearchStatus)
                .overallStatus(overallStatus)
                .build();
    }


    /**
     * Check PostgreSQL connectivity from Auth Service.
     */
    private String checkDatabase() {

        try (Connection connection =
                     dataSource.getConnection()) {

            if (connection.isValid(2)) {
                return "UP";
            }

            return "DOWN";

        } catch (Exception ignored) {
            return "DOWN";
        }
    }


    /**
     * Normalize health status values.
     */
    private String normalizeStatus(
            String status
    ) {

        if ("UP".equalsIgnoreCase(status)) {
            return "UP";
        }

        return "DOWN";
    }


    /**
     * Determine overall platform health.
     */
    private String determineOverallStatus(
            String authStatus,
            String databaseStatus,
            String aiStatus,
            String redisStatus,
            String vectorSearchStatus
    ) {

        if ("UP".equalsIgnoreCase(authStatus)
                && "UP".equalsIgnoreCase(databaseStatus)
                && "UP".equalsIgnoreCase(aiStatus)
                && "UP".equalsIgnoreCase(redisStatus)
                && "UP".equalsIgnoreCase(vectorSearchStatus)) {

            return "HEALTHY";
        }

        return "DEGRADED";
    }


    /**
     * Build hospital summary with real data from the shared database.
     *
     * Users are managed by the Auth Service JPA layer.
     * Patients and trials are managed by the AI Service,
     * so their counts are read directly from the shared database.
     */
    private HospitalSummaryResponse mapHospital(
            Hospital hospital
    ) {

        UUID hospitalId = hospital.getId();

        return HospitalSummaryResponse.builder()
                .hospitalId(
                        hospitalId
                )
                .hospitalName(
                        hospital.getName()
                )
                .totalUsers(
                        userRepository.countByHospitalId(
                                hospitalId
                        )
                )
                .totalPatients(
                        countPatientsByHospital(
                                hospitalId
                        )
                )
                .activeTrials(
                        countActiveTrialsByHospital(
                                hospitalId
                        )
                )
                .matchesGenerated(
                        countEligibilityEvaluationsByHospital(
                                hospitalId
                        )
                )
                .build();
    }


    /**
     * Count patients belonging to a hospital.
     *
     * Patients are owned by the AI service
     * (FastAPI/SQLAlchemy), not this service's JPA layer.
     * Therefore the shared patients table is queried directly
     * through the existing DataSource.
     */
    private Long countPatientsByHospital(
            UUID hospitalId
    ) {

        String sql =
                "SELECT COUNT(*) " +
                "FROM patients " +
                "WHERE hospital_id = ?";

        try (Connection connection =
                     dataSource.getConnection();
             PreparedStatement statement =
                     connection.prepareStatement(sql)) {

            statement.setObject(
                    1,
                    hospitalId
            );

            try (ResultSet resultSet =
                         statement.executeQuery()) {

                return resultSet.next()
                        ? resultSet.getLong(1)
                        : 0L;
            }

        } catch (Exception ignored) {
            return 0L;
        }
    }


    /**
     * Count active clinical trials belonging to a hospital.
     *
     * Active trials are currently defined as trials
     * whose status is 'Recruiting'.
     */
    private Long countActiveTrialsByHospital(
            UUID hospitalId
    ) {

        String sql =
                "SELECT COUNT(*) " +
                "FROM trials " +
                "WHERE hospital_id = ? " +
                "AND status = 'Recruiting'";

        try (Connection connection =
                     dataSource.getConnection();
             PreparedStatement statement =
                     connection.prepareStatement(sql)) {

            statement.setObject(
                    1,
                    hospitalId
            );

            try (ResultSet resultSet =
                         statement.executeQuery()) {

                return resultSet.next()
                        ? resultSet.getLong(1)
                        : 0L;
            }

        } catch (Exception ignored) {
            return 0L;
        }
    }


    /**
     * Count generated eligibility evaluations for a hospital.
     *
     * There is currently no persisted Match/MatchResult entity.
     * Therefore ELIGIBILITY_EVALUATED audit events are used
     * as the current source for the matches-generated count.
     */
    private Long countEligibilityEvaluationsByHospital(
            UUID hospitalId
    ) {

        String sql =
                "SELECT COUNT(*) " +
                "FROM audit_logs " +
                "WHERE hospital_id = ? " +
                "AND action = 'ELIGIBILITY_EVALUATED'";

        try (Connection connection =
                     dataSource.getConnection();
             PreparedStatement statement =
                     connection.prepareStatement(sql)) {

            statement.setObject(
                    1,
                    hospitalId
            );

            try (ResultSet resultSet =
                         statement.executeQuery()) {

                return resultSet.next()
                        ? resultSet.getLong(1)
                        : 0L;
            }

        } catch (Exception ignored) {
            return 0L;
        }
    }
}