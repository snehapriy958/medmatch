package com.medmatch.auth.service;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.medmatch.auth.audit.AuditAction;
import com.medmatch.auth.dto.LoginRequest;
import com.medmatch.auth.dto.LoginResponse;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.BusinessValidationException;
import com.medmatch.auth.jwt.JwtService;
import com.medmatch.auth.repository.UserRepository;

@Service
public class AuthService {

    private static final String INVALID_CREDENTIALS =
            "Invalid username or password";

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuditLogService auditLogService;

    public AuthService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            AuditLogService auditLogService
    ) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.auditLogService = auditLogService;
    }

    public LoginResponse login(LoginRequest request) {

        System.out.println("--------------------------------");
        System.out.println("Username received: " + request.getUsername());

        User user = userRepository.findByUsername(request.getUsername())
                .orElseThrow(() -> {
                    System.out.println("User not found.");
                    return new BusinessValidationException(INVALID_CREDENTIALS);
                });

        boolean matches = passwordEncoder.matches(
                request.getPassword(),
                user.getPassword()
        );

        if (!matches) {
            System.out.println("Login Failed");
            throw new BusinessValidationException(INVALID_CREDENTIALS);
        }

        String accessToken = jwtService.generateToken(user);

        // Audit successful login
        auditLogService.log(
                AuditAction.LOGIN,
                "AUTH",
                user.getId(),
                user,
                user.getHospital(),
                "User logged in",
                null
        );

        return new LoginResponse(
                accessToken,
                "Bearer",
                jwtService.getAccessTokenExpiry()
        );
    }
}