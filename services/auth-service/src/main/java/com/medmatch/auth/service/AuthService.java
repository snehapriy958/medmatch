package com.medmatch.auth.service;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.medmatch.auth.audit.AuditAction;
import com.medmatch.auth.dto.LoginRequest;
import com.medmatch.auth.dto.LoginResponse;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.BusinessValidationException;
import com.medmatch.auth.jwt.JwtService;
import com.medmatch.auth.metrics.MetricsService;
import com.medmatch.auth.repository.UserRepository;

import io.micrometer.core.instrument.Timer;

@Service
public class AuthService {

    private static final String INVALID_CREDENTIALS =
            "Invalid username or password";

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuditLogService auditLogService;
    private final MetricsService metricsService;

    public AuthService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            AuditLogService auditLogService,
            MetricsService metricsService
    ) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.auditLogService = auditLogService;
        this.metricsService = metricsService;
    }

    public LoginResponse login(LoginRequest request) {

        Timer.Sample timer = metricsService.startLoginTimer();

        try {

                System.out.println("--------------------------------");
                System.out.println("Username received: " + request.getUsername());

                User user = userRepository.findByUsername(request.getUsername())
                        .orElseThrow(() -> {
                                System.out.println("User not found.");
                                metricsService.loginFailure();
                                return new BusinessValidationException(INVALID_CREDENTIALS);
                        });

                boolean matches = passwordEncoder.matches(
                        request.getPassword(),
                        user.getPassword()
                );

                if (!matches) {
                        System.out.println("Login Failed");
                        metricsService.loginFailure();
                        throw new BusinessValidationException(INVALID_CREDENTIALS);
                }

                String accessToken = jwtService.generateToken(user);

                auditLogService.log(
                        AuditAction.LOGIN,
                        "AUTH",
                        user.getId(),
                        user,
                        user.getHospital(),
                        "User logged in",
                        null
                );

                metricsService.loginSuccess();

                return new LoginResponse(
                        accessToken,
                        "Bearer",
                        jwtService.getAccessTokenExpiry()
                );

        } finally {

                metricsService.stopLoginTimer(timer);

        }
    }
}