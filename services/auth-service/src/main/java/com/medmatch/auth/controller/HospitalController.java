package com.medmatch.auth.controller;

import java.net.URI;
import java.util.List;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.medmatch.auth.dto.HospitalCreateRequest;
import com.medmatch.auth.dto.HospitalResponse;
import com.medmatch.auth.dto.HospitalUpdateRequest;
import com.medmatch.auth.service.HospitalService;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/auth/hospitals")
public class HospitalController {

    private final HospitalService hospitalService;

    public HospitalController(HospitalService hospitalService) {
        this.hospitalService = hospitalService;
    }

    /**
     * Create a new hospital.
     */
    @PostMapping
    public ResponseEntity<HospitalResponse> createHospital(
            @Valid @RequestBody HospitalCreateRequest request) {

        HospitalResponse response = hospitalService.createHospital(request);

        URI location = URI.create("/hospitals/" + response.getId());

        return ResponseEntity
                .created(location)
                .body(response);
    }

    /**
     * Get all hospitals.
     */
    @GetMapping
    public ResponseEntity<List<HospitalResponse>> getAllHospitals() {

        return ResponseEntity.ok(
                hospitalService.getAllHospitals()
        );
    }

    /**
     * Get hospital by ID.
     */
    @GetMapping("/{id}")
    public ResponseEntity<HospitalResponse> getHospitalById(
            @PathVariable UUID id) {

        return ResponseEntity.ok(
                hospitalService.getHospitalById(id)
        );
    }

    /**
     * Update hospital.
     */
    @PutMapping("/{id}")
    public ResponseEntity<HospitalResponse> updateHospital(
            @PathVariable UUID id,
            @Valid @RequestBody HospitalUpdateRequest request) {

        return ResponseEntity.ok(
                hospitalService.updateHospital(id, request)
        );
    }

    /**
     * Delete hospital by ID.
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteHospital(
            @PathVariable UUID id) {

        hospitalService.deleteHospital(id);

        return ResponseEntity.noContent().build();
    }
}