package com.medmatch.auth.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.medmatch.auth.entity.Hospital;


public interface HospitalRepository extends JpaRepository<Hospital, UUID> {

    /**
     * Retrieves a hospital by its unique business code.
     */
    Optional<Hospital> findByCode(String code);


    /**
     * Checks whether a hospital with the given code already exists.
     */
    boolean existsByCode(String code);

}