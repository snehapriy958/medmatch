package com.medmatch.auth.repository;

import com.medmatch.auth.entity.Hospital;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface HospitalRepository extends JpaRepository<Hospital, UUID> {

    Optional<Hospital> findByCode(String code);

    boolean existsByCode(String code);

    List<Hospital> findByActiveTrue();
}