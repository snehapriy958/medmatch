package com.medmatch.auth.service;

import java.util.List;
import java.util.UUID;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.medmatch.auth.audit.AuditAction;
import com.medmatch.auth.dto.HospitalCreateRequest;
import com.medmatch.auth.dto.HospitalResponse;
import com.medmatch.auth.dto.HospitalUpdateRequest;
import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.BusinessValidationException;
import com.medmatch.auth.exception.DuplicateResourceException;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.UserRepository;
import com.medmatch.auth.security.SecurityUtils;

@Service
@Transactional(readOnly = true)
public class HospitalService {

    private final HospitalRepository hospitalRepository;
    private final UserRepository userRepository;
    private final AuditLogService auditLogService;
    private final SecurityUtils securityUtils;

    public HospitalService(
            HospitalRepository hospitalRepository,
            UserRepository userRepository,
            AuditLogService auditLogService,
            SecurityUtils securityUtils
    ) {
        this.hospitalRepository = hospitalRepository;
        this.userRepository = userRepository;
        this.auditLogService = auditLogService;
        this.securityUtils = securityUtils;
    }

    /**
     * Returns the hospital with the given code.
     */
    public Hospital getHospitalByCode(String code) {

        return hospitalRepository.findByCode(code)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found with code: " + code));
    }

    /**
     * Returns all hospitals.
     */
    public List<HospitalResponse> getAllHospitals() {

        return hospitalRepository.findAll()
                .stream()
                .map(this::toResponse)
                .toList();
    }

    /**
     * Returns a hospital by ID.
     */
    public HospitalResponse getHospitalById(UUID id) {

        Hospital hospital = hospitalRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found with id: " + id));

        return toResponse(hospital);
    }

    /**
     * Returns the Hospital entity by ID.
     */
    public Hospital getHospitalByIdEntity(UUID id) {

        return hospitalRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found with id: " + id));
    }

    /**
     * Creates a new hospital.
     */
    @Transactional
    public HospitalResponse createHospital(HospitalCreateRequest request) {

        if (hospitalRepository.existsByCode(request.getCode())) {
            throw new DuplicateResourceException(
                    "Hospital code already exists.");
        }

        Hospital hospital = new Hospital();

        hospital.setCode(request.getCode());
        hospital.setName(request.getName());
        hospital.setAddress(request.getAddress());

        try {

            hospital = hospitalRepository.save(hospital);

        } catch (DataIntegrityViolationException ex) {

            throw new DuplicateResourceException(
                    "Hospital code already exists."
            );
        }

        logHospitalAudit(
                AuditAction.CREATE_HOSPITAL,
                hospital,
                "Created hospital: " + hospital.getName()
        );

        return toResponse(hospital);
    }

    /**
     * Updates an existing hospital.
     */
    @Transactional
    public HospitalResponse updateHospital(
            UUID id,
            HospitalUpdateRequest request
    ) {

        Hospital hospital = hospitalRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found with id: " + id));

        if (!hospital.getCode().equals(request.getCode())
                && hospitalRepository.existsByCode(request.getCode())) {

            throw new DuplicateResourceException(
                    "Hospital code already exists.");
        }

        hospital.setCode(request.getCode());
        hospital.setName(request.getName());
        hospital.setAddress(request.getAddress());

        try {

            hospital = hospitalRepository.save(hospital);

        } catch (DataIntegrityViolationException ex) {

            throw new DuplicateResourceException(
                    "Hospital code already exists."
            );
        }

        logHospitalAudit(
                AuditAction.UPDATE_HOSPITAL,
                hospital,
                "Updated hospital: " + hospital.getName()
        );

        return toResponse(hospital);
    }

    /**
     * Deletes a hospital.
     */
    @Transactional
    public void deleteHospital(UUID id) {

        Hospital hospital = hospitalRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found with id: " + id));

        // Prevent deleting hospitals that still have users assigned.
        if (userRepository.existsByHospital(hospital)) {
            throw new BusinessValidationException(
                    "Cannot delete hospital because users are assigned to it."
            );
        }

        logHospitalAudit(
                AuditAction.DELETE_HOSPITAL,
                hospital,
                "Deleted hospital: " + hospital.getName()
        );

        hospitalRepository.delete(hospital);
    }

    /**
     * Creates an audit log for hospital-related operations.
     */
    private void logHospitalAudit(
            AuditAction action,
            Hospital hospital,
            String details
    ) {

        User currentUser = securityUtils.getCurrentUser();

        auditLogService.log(
                action,
                "HOSPITAL",
                hospital.getId(),
                currentUser,
                hospital,
                details,
                null
        );
    }

    /**
     * Converts Hospital entity to DTO.
     */
    private HospitalResponse toResponse(Hospital hospital) {

        return new HospitalResponse(
                hospital.getId(),
                hospital.getCode(),
                hospital.getName(),
                hospital.getAddress()
        );
    }

    /**
     * Returns the Hospital entity by hospital code.
     */
    public Hospital getHospitalByCodeEntity(String code) {

        return hospitalRepository.findByCode(code)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found with code: " + code
                        ));
    }
}