package com.medmatch.auth.entity;


import com.fasterxml.jackson.annotation.JsonIgnore;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;


import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;



@Entity
@Table(name = "roles")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Role {


    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @JdbcTypeCode(SqlTypes.UUID)
    @Column(
            name = "id",
            updatable = false,
            nullable = false
    )
    private UUID id;




    /*
     * Role names are stored as STRING.
     *
     * Example:
     * SYSTEM_ADMIN
     * HOSPITAL_ADMIN
     * PHYSICIAN
     * PATIENT
     *
     * Avoids enum ordinal corruption.
     */
    @Enumerated(EnumType.STRING)
    @Column(
            name = "name",
            nullable = false,
            unique = true
    )
    private RoleType name;




    @CreationTimestamp
    @Column(
            name = "created_at",
            nullable = false,
            updatable = false
    )
    private LocalDateTime createdAt;




    /*
     * Users having this role.
     *
     * Inverse side:
     *
     * User.role
     *
     * No cascade intentionally.
     */
    @JsonIgnore
    @OneToMany(
            mappedBy = "role",
            fetch = FetchType.LAZY
    )
    @Builder.Default
    private List<User> users = new ArrayList<>();

}