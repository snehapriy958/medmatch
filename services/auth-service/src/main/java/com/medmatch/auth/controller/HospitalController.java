package com.medmatch.auth.controller;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.service.HospitalService;

import lombok.RequiredArgsConstructor;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.security.access.prepost.PreAuthorize;

import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;


@RestController
@RequestMapping("/hospitals")
@RequiredArgsConstructor
public class HospitalController {


    private final HospitalService hospitalService;



    @PostMapping
    @PreAuthorize("hasRole('SYSTEM_ADMIN')")
    public ResponseEntity<Hospital> createHospital(
            @Valid @RequestBody Hospital hospital
    ){

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(
                    hospitalService.createHospital(hospital)
                );
    }



    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('SYSTEM_ADMIN','HOSPITAL_ADMIN')")
    public ResponseEntity<Hospital> getHospitalById(
            @PathVariable UUID id
    ){

        return ResponseEntity.ok(
                hospitalService.getHospitalById(id)
        );
    }



    @GetMapping
    @PreAuthorize("hasRole('SYSTEM_ADMIN')")
    public ResponseEntity<List<Hospital>> getAllHospitals(){

        return ResponseEntity.ok(
                hospitalService.getAllHospitals()
        );
    }



    @GetMapping("/active")
    @PreAuthorize("hasRole('SYSTEM_ADMIN')")
    public ResponseEntity<List<Hospital>> getActiveHospitals(){

        return ResponseEntity.ok(
                hospitalService.getActiveHospitals()
        );
    }



    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('SYSTEM_ADMIN','HOSPITAL_ADMIN')")
    public ResponseEntity<Hospital> updateHospital(
            @PathVariable UUID id,
            @Valid @RequestBody Hospital hospital
    ){

        return ResponseEntity.ok(
                hospitalService.updateHospital(id,hospital)
        );
    }



    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('SYSTEM_ADMIN')")
    public ResponseEntity<Void> deactivateHospital(
            @PathVariable UUID id
    ){

        hospitalService.deactivateHospital(id);

        return ResponseEntity.noContent().build();
    }

}