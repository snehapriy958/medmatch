package com.medmatch.auth.service;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.exception.DuplicateResourceException;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.HospitalRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class HospitalServiceImpl implements HospitalService {

    private final HospitalRepository hospitalRepository;


    @Override
    @Transactional(readOnly = true)
    public Hospital getHospitalById(UUID id) {

        return hospitalRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found"
                        )
                );
    }


    @Override
    @Transactional
    public Hospital createHospital(Hospital hospital) {


        if (hospitalRepository.existsByCode(
                hospital.getCode()
        )) {

            throw new DuplicateResourceException(
                    "Hospital code already exists"
            );
        }


        return hospitalRepository.save(hospital);
    }



    @Override
    @Transactional(readOnly = true)
    public List<Hospital> getAllHospitals() {

        return hospitalRepository.findAll();
    }



    @Override
    @Transactional(readOnly = true)
    public List<Hospital> getActiveHospitals() {

        return hospitalRepository.findByActiveTrue();
    }



    @Override
    @Transactional
    public Hospital updateHospital(
            UUID id,
            Hospital updatedHospital
    ) {


        Hospital hospital =
                getHospitalById(id);



        hospital.setName(
                updatedHospital.getName()
        );


        hospital.setAddress(
                updatedHospital.getAddress()
        );


        return hospitalRepository.save(hospital);
    }




    @Override
    @Transactional
    public void deactivateHospital(UUID id) {


        Hospital hospital =
                getHospitalById(id);


        hospital.setActive(false);


        hospitalRepository.save(hospital);
    }




    @Override
    @Transactional(readOnly = true)
    public boolean existsByCode(String code) {

        return hospitalRepository.existsByCode(code);
    }

}