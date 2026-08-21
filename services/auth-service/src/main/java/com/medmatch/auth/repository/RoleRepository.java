package com.medmatch.auth.repository;

import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.RoleType;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RoleRepository extends JpaRepository<Role, UUID> {

    Optional<Role> findByName(RoleType name);

    boolean existsByName(RoleType name);
}