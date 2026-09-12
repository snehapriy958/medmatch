package com.medmatch.auth.service;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.DuplicateResourceException;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class HospitalServiceImpl implements HospitalService {

    private final HospitalRepository hospitalRepository;
    private final UserRepository userRepository;


    @Override
    @Transactional(readOnly = true)
    public Hospital getHospitalById(UUID id) {

        Hospital hospital = hospitalRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found"
                        )
                );

        // NOTE: previously unguarded — any authenticated HOSPITAL_ADMIN
        // (this endpoint's @PreAuthorize allows SYSTEM_ADMIN and
        // HOSPITAL_ADMIN) could read *any* hospital by id, and since
        // updateHospital()/deactivateHospital() both call this method
        // internally, a HOSPITAL_ADMIN could also edit another
        // hospital's name/address. Fixed with the same tenant-boundary
        // pattern UserServiceImpl.getUserById already uses.
        assertHospitalAccess(id);

        return hospital;
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


    private void assertHospitalAccess(UUID hospitalId) {

        Authentication authentication =
                SecurityContextHolder.getContext().getAuthentication();

        boolean isSystemAdmin = authentication.getAuthorities().stream()
                .anyMatch(authority ->
                        authority.getAuthority().equals("ROLE_SYSTEM_ADMIN"));

        if (isSystemAdmin) {
            return;
        }

        User currentUser = userRepository.findByEmail(authentication.getName())
                .orElseThrow(() ->
                        new ResourceNotFoundException("Current user not found"));

        if (!currentUser.getHospital().getId().equals(hospitalId)) {
            throw new AccessDeniedException("Cannot access another hospital");
        }
    }

}