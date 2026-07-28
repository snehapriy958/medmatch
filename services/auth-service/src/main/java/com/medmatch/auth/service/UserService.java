package com.medmatch.auth.service;

import java.util.List;
import java.util.UUID;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.medmatch.auth.audit.AuditAction;
import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;
import com.medmatch.auth.dto.UserUpdateRequest;
import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.DuplicateResourceException;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.metrics.MetricsService;
import com.medmatch.auth.repository.UserRepository;
import com.medmatch.auth.security.SecurityUtils;

@Service
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;
    private final HospitalService hospitalService;
    private final PasswordEncoder passwordEncoder;
    private final AuditLogService auditLogService;
    private final SecurityUtils securityUtils;
    private final MetricsService metricsService;

    public UserService(
            UserRepository userRepository,
            HospitalService hospitalService,
            PasswordEncoder passwordEncoder,
            AuditLogService auditLogService,
            SecurityUtils securityUtils,
            MetricsService metricsService
    ) {
        this.userRepository = userRepository;
        this.hospitalService = hospitalService;
        this.passwordEncoder = passwordEncoder;
        this.auditLogService = auditLogService;
        this.securityUtils = securityUtils;
        this.metricsService = metricsService;
    }

    /**
     * Registers a new user.
     */
    @Transactional
    public User register(RegisterRequest request) {

        if (userRepository.existsByUsername(request.getUsername())) {
            throw new DuplicateResourceException("Username already exists.");
        }

        if (userRepository.existsByEmail(request.getEmail())) {
            throw new DuplicateResourceException("Email already exists.");
        }

        Hospital hospital =
                hospitalService.getHospitalByCodeEntity(request.getHospitalCode());

        User user = new User(
                request.getUsername(),
                request.getEmail(),
                request.getPassword(),
                request.getRole()
        );

        user.setHospital(hospital);

        user.setPassword(
                passwordEncoder.encode(user.getPassword())
        );

        try {

            User savedUser = userRepository.save(user);

            metricsService.registration();
            logUserAudit(
                    AuditAction.CREATE_USER,
                    savedUser,
                    "Created user: " + savedUser.getUsername()
            );

            return savedUser;

        } catch (DataIntegrityViolationException ex) {

            throw new DuplicateResourceException(
                    "Username or email already exists."
            );
        }
    }

    /**
     * Returns all users.
     */
    public List<UserResponse> getAllUsers() {

        return userRepository.findAll()
                .stream()
                .map(this::toResponse)
                .toList();
    }

    /**
     * Returns a user by ID.
     */
    public UserResponse getUserById(UUID id) {

        User user = userRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "User not found with id: " + id));

        return toResponse(user);
    }

    /**
     * Updates an existing user.
     */
    @Transactional
    public UserResponse updateUser(
            UUID id,
            UserUpdateRequest request
    ) {

        User user = userRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "User not found with id: " + id));

        if (!user.getUsername().equals(request.getUsername())
                && userRepository.existsByUsername(request.getUsername())) {

            throw new DuplicateResourceException("Username already exists.");
        }

        if (!user.getEmail().equals(request.getEmail())
                && userRepository.existsByEmail(request.getEmail())) {

            throw new DuplicateResourceException("Email already exists.");
        }

        Hospital hospital =
                hospitalService.getHospitalByCodeEntity(request.getHospitalCode());

        user.setUsername(request.getUsername());
        user.setEmail(request.getEmail());
        user.setRole(request.getRole());
        user.setHospital(hospital);

        try {

            user = userRepository.save(user);

        } catch (DataIntegrityViolationException ex) {

            throw new DuplicateResourceException(
                    "Username or email already exists."
            );
        }

        logUserAudit(
                AuditAction.UPDATE_USER,
                user,
                "Updated user: " + user.getUsername()
        );

        return toResponse(user);
    }

    /**
     * Deletes a user.
     */
    @Transactional
    public void deleteUser(UUID id) {

        User user = userRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "User not found with id: " + id));

        logUserAudit(
                AuditAction.DELETE_USER,
                user,
                "Deleted user: " + user.getUsername()
        );

        userRepository.delete(user);
    }

    /**
     * Creates an audit log for user-related operations.
     */
    private void logUserAudit(
            AuditAction action,
            User affectedUser,
            String details
    ) {

        User currentUser = securityUtils.getCurrentUser();

        auditLogService.log(
                action,
                "USER",
                affectedUser.getId(),
                currentUser,
                affectedUser.getHospital(),
                details,
                null
        );
    }

    /**
     * Converts User entity to DTO.
     */
    private UserResponse toResponse(User user) {

        return new UserResponse(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.getRole(),
                user.getHospital().getId(),
                user.getHospital().getCode(),
                user.getHospital().getName()
        );
    }
}