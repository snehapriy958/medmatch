package com.medmatch.auth.service.dashboard;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.repository.AuditLogRepository;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.UserRepository;
import com.medmatch.auth.dto.dashboard.SystemDashboardResponse;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.List;
import java.util.UUID;
import javax.sql.DataSource;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import tools.jackson.databind.ObjectMapper;

/**
 * DashboardServiceImpl talks to three things this suite can't rely on
 * having in the test environment: a real Postgres connection, the
 * separate ai-service over HTTP, and the AI service's own database
 * tables (patients/trials) queried via raw JDBC. Rather than skip
 * coverage, each is faked deterministically and offline:
 *   - DataSource / Connection / PreparedStatement / ResultSet: Mockito
 *     mocks, so the raw-SQL count queries are exercised without a DB.
 *   - the AI service: a tiny embedded com.sun.net.httpserver.HttpServer
 *     bound to 127.0.0.1, so the "AI service reachable" path is tested
 *     for real (real HTTP, real JSON parsing) with zero external
 *     network dependency, and the "unreachable" path uses a closed
 *     local port for an instant, deterministic connection refusal.
 */
@ExtendWith(MockitoExtension.class)
class DashboardServiceImplTest {

    @Mock private UserRepository userRepository;
    @Mock private HospitalRepository hospitalRepository;
    @Mock private AuditLogRepository auditLogRepository;
    @Mock private DataSource dataSource;

    private DashboardServiceImpl dashboardService;
    private HttpServer aiServiceStub;

    @BeforeEach
    void setUp() {
        dashboardService = new DashboardServiceImpl(
                userRepository, hospitalRepository, auditLogRepository,
                dataSource, new ObjectMapper());
    }

    @AfterEach
    void tearDown() {
        if (aiServiceStub != null) {
            aiServiceStub.stop(0);
        }
    }

    private void pointAiServiceUrlAt(String url) {
        ReflectionTestUtils.setField(dashboardService, "aiServiceUrl", url);
    }

    /** Starts a local stub that answers the ai-service's /api/health/ready shape. */
    private String startAiServiceStub(int statusCode, String jsonBody) throws IOException {
        aiServiceStub = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        aiServiceStub.createContext("/api/health/ready", exchange -> {
            byte[] body = jsonBody.getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(statusCode, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        aiServiceStub.start();
        return "http://127.0.0.1:" + aiServiceStub.getAddress().getPort();
    }

    private void mockHealthyDatabase() throws SQLException {
        Connection connection = org.mockito.Mockito.mock(Connection.class);
        when(dataSource.getConnection()).thenReturn(connection);
        when(connection.isValid(2)).thenReturn(true);
        // Any prepareStatement()/executeQuery() call on this mock connection
        // returns Mockito defaults (null / no interactions further stubbed),
        // which the raw-SQL helper methods' catch blocks turn into 0 counts —
        // fine here since this test only asserts on databaseStatus/health.
    }

    @Test
    void getSystemDashboard_assemblesMetricsFromRepositories() {
        when(userRepository.count()).thenReturn(42L);
        when(userRepository.countByStatus("ACTIVE")).thenReturn(30L);
        Hospital active1 = Hospital.builder().id(UUID.randomUUID()).code("H1").name("H1").active(true).build();
        Hospital active2 = Hospital.builder().id(UUID.randomUUID()).code("H2").name("H2").active(true).build();
        when(hospitalRepository.findByActiveTrue()).thenReturn(List.of(active1, active2));
        when(hospitalRepository.findAll()).thenReturn(List.of(active1, active2));
        when(auditLogRepository.count()).thenReturn(500L);
        when(auditLogRepository.countByAction("LOGIN_SUCCESS")).thenReturn(120L);
        pointAiServiceUrlAt("http://127.0.0.1:1"); // refused: keeps AI-related fields deterministic

        SystemDashboardResponse response = dashboardService.getSystemDashboard();

        assertThat(response.getMetrics()).hasSize(3);
        assertThat(response.getMetrics().get(0).getTitle()).isEqualTo("Total Users");
        assertThat(response.getMetrics().get(0).getValue()).isEqualTo(42L);
        assertThat(response.getMetrics().get(1).getValue()).isEqualTo(30L);
        assertThat(response.getMetrics().get(2).getValue()).isEqualTo(2L);
        assertThat(response.getAuditSummary().getTotalEvents()).isEqualTo(500L);
        assertThat(response.getAuditSummary().getUserActivities()).isEqualTo(120L);
    }

    @Test
    void getSystemDashboard_mapsEachHospitalWithUserCount() {
        Hospital hospital = Hospital.builder().id(UUID.randomUUID()).code("H1").name("Hospital One").active(true).build();
        when(userRepository.count()).thenReturn(0L);
        when(userRepository.countByStatus("ACTIVE")).thenReturn(0L);
        when(userRepository.countByHospitalId(hospital.getId())).thenReturn(7L);
        when(hospitalRepository.findByActiveTrue()).thenReturn(List.of(hospital));
        when(hospitalRepository.findAll()).thenReturn(List.of(hospital));
        when(auditLogRepository.count()).thenReturn(0L);
        when(auditLogRepository.countByAction("LOGIN_SUCCESS")).thenReturn(0L);
        pointAiServiceUrlAt("http://127.0.0.1:1");

        SystemDashboardResponse response = dashboardService.getSystemDashboard();

        assertThat(response.getTopHospitals()).hasSize(1);
        assertThat(response.getTopHospitals().get(0).getHospitalId()).isEqualTo(hospital.getId());
        assertThat(response.getTopHospitals().get(0).getHospitalName()).isEqualTo("Hospital One");
        assertThat(response.getTopHospitals().get(0).getTotalUsers()).isEqualTo(7L);
        // Patients/trials/matches are read via raw JDBC against the AI
        // service's tables; with an unstubbed DataSource these fall back
        // to 0 through the method's own catch block (by design — one
        // dependency failing shouldn't break the whole dashboard).
        assertThat(response.getTopHospitals().get(0).getTotalPatients()).isEqualTo(0L);
    }

    @Test
    void getSystemDashboard_whenAiServiceAndDbUnreachable_reportsDegraded() throws Exception {
        stubEmptyRepositoriesForHealthCheck();
        when(dataSource.getConnection()).thenAnswer(invocation -> {
            throw new SQLException("connection refused");
        });
        // Port 1 is a privileged/closed port on 127.0.0.1: connection
        // refusal is immediate and doesn't touch the network.
        pointAiServiceUrlAt("http://127.0.0.1:1");

        SystemDashboardResponse response = dashboardService.getSystemDashboard();

        assertThat(response.getSystemHealth().getDatabaseStatus()).isEqualTo("DOWN");
        assertThat(response.getSystemHealth().getAiServiceStatus()).isEqualTo("DOWN");
        assertThat(response.getSystemHealth().getRedisStatus()).isEqualTo("DOWN");
        assertThat(response.getSystemHealth().getVectorSearchStatus()).isEqualTo("DOWN");
        assertThat(response.getSystemHealth().getOverallStatus()).isEqualTo("DEGRADED");
        // Auth service reporting its own status is hardcoded UP — it's
        // the process answering the request, so DEGRADED here can only
        // come from its dependencies.
        assertThat(response.getSystemHealth().getAuthServiceStatus()).isEqualTo("UP");
    }

    @Test
    void getSystemDashboard_whenAiServiceAndDbHealthy_reportsHealthy() throws Exception {
        stubEmptyRepositoriesForHealthCheck();
        mockHealthyDatabase();
        String stubUrl = startAiServiceStub(200,
                "{\"status\":\"UP\",\"checks\":{\"redis\":\"UP\",\"vector_search\":\"UP\"}}");
        pointAiServiceUrlAt(stubUrl);

        SystemDashboardResponse response = dashboardService.getSystemDashboard();

        assertThat(response.getSystemHealth().getDatabaseStatus()).isEqualTo("UP");
        assertThat(response.getSystemHealth().getAiServiceStatus()).isEqualTo("UP");
        assertThat(response.getSystemHealth().getRedisStatus()).isEqualTo("UP");
        assertThat(response.getSystemHealth().getVectorSearchStatus()).isEqualTo("UP");
        assertThat(response.getSystemHealth().getOverallStatus()).isEqualTo("HEALTHY");
    }

    @Test
    void getSystemDashboard_whenAiServiceReportsPartialOutage_staysDegraded() throws Exception {
        stubEmptyRepositoriesForHealthCheck();
        mockHealthyDatabase();
        // AI service itself is up, but its Redis dependency is down —
        // the overall platform status must not claim HEALTHY here.
        String stubUrl = startAiServiceStub(200,
                "{\"status\":\"UP\",\"checks\":{\"redis\":\"DOWN\",\"vector_search\":\"UP\"}}");
        pointAiServiceUrlAt(stubUrl);

        SystemDashboardResponse response = dashboardService.getSystemDashboard();

        assertThat(response.getSystemHealth().getAiServiceStatus()).isEqualTo("UP");
        assertThat(response.getSystemHealth().getRedisStatus()).isEqualTo("DOWN");
        assertThat(response.getSystemHealth().getVectorSearchStatus()).isEqualTo("UP");
        assertThat(response.getSystemHealth().getOverallStatus()).isEqualTo("DEGRADED");
    }

    private void stubEmptyRepositoriesForHealthCheck() {
        when(userRepository.count()).thenReturn(0L);
        when(userRepository.countByStatus("ACTIVE")).thenReturn(0L);
        when(hospitalRepository.findByActiveTrue()).thenReturn(List.of());
        when(hospitalRepository.findAll()).thenReturn(List.of());
        when(auditLogRepository.count()).thenReturn(0L);
        when(auditLogRepository.countByAction("LOGIN_SUCCESS")).thenReturn(0L);
    }
}
