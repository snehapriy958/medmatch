// package com.medmatch.auth.repository;

// import java.util.Optional;
// import java.util.UUID;

// import org.springframework.data.jpa.repository.JpaRepository;

// import com.medmatch.auth.entity.Hospital;
// import com.medmatch.auth.entity.User;


// public interface UserRepository extends JpaRepository<User, UUID> {

//     Optional<User> findByUsername(String username);

//     Optional<User> findByEmail(String email);

//     boolean existsByUsername(String username);

//     boolean existsByEmail(String email);

//     boolean existsByHospital(Hospital hospital);

// }

package com.medmatch.auth.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.User;

public interface UserRepository extends JpaRepository<User, UUID> {

    @EntityGraph(attributePaths = "hospital")
    Optional<User> findByUsername(String username);

    @EntityGraph(attributePaths = "hospital")
    Optional<User> findByEmail(String email);

    boolean existsByUsername(String username);

    boolean existsByEmail(String email);

    boolean existsByHospital(Hospital hospital);
}