package com.medmatch.auth.repository;


import com.medmatch.auth.entity.RoleType;
import com.medmatch.auth.entity.User;


import org.springframework.data.jpa.repository.JpaRepository;


import java.util.List;
import java.util.Optional;
import java.util.UUID;



public interface UserRepository extends JpaRepository<User, UUID> {


    Optional<User> findByEmail(String email);


    boolean existsByEmail(String email);


    List<User> findByHospitalId(UUID hospitalId);



    long countByHospitalId(UUID hospitalId);



    long countByHospitalIdAndEnabledTrue(UUID hospitalId);



    long countByRoleName(RoleType role);



    long countByStatus(String status);

}