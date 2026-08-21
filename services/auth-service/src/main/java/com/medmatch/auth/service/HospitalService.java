package com.medmatch.auth.service;

import com.medmatch.auth.entity.Hospital;

import java.util.List;
import java.util.UUID;

public interface HospitalService {

    Hospital createHospital(Hospital hospital);

    Hospital getHospitalById(UUID id);

    List<Hospital> getAllHospitals();

    List<Hospital> getActiveHospitals();

    Hospital updateHospital(UUID id, Hospital hospital);

    void deactivateHospital(UUID id);

    boolean existsByCode(String code);

}