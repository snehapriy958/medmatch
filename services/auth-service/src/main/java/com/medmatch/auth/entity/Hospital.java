package com.medmatch.auth.entity;


import com.fasterxml.jackson.annotation.JsonIgnore;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
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
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;



@Entity
@Table(name = "hospitals")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Hospital {


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
     * Unique hospital identifier.
     *
     * Example:
     * MANIPAL001
     * APOLLO001
     */
    @Column(
            name = "code",
            nullable = false,
            unique = true
    )
    private String code;



    @Column(
            name = "name",
            nullable = false
    )
    private String name;



    @Column(name = "address")
    private String address;



    /*
     * Soft delete flag.
     *
     * Used for:
     * - active hospital dashboard
     * - preventing new registrations
     * - hospital lifecycle management
     */
    @Builder.Default
    @Column(
            name = "active",
            nullable = false
    )
    private Boolean active = true;



    @CreationTimestamp
    @Column(
            name = "created_at",
            nullable = false,
            updatable = false
    )
    private LocalDateTime createdAt;



    @UpdateTimestamp
    @Column(
            name = "updated_at",
            nullable = false
    )
    private LocalDateTime updatedAt;




    /*
     * Users belonging to this hospital.
     *
     * Used for:
     * - hospital dashboard
     * - user management
     * - tenant isolation
     *
     * User table owns the relationship through:
     *
     * User.hospital
     *
     * No cascade intentionally.
     */
    @JsonIgnore
    @OneToMany(
            mappedBy = "hospital",
            fetch = FetchType.LAZY
    )
    @Builder.Default
    private List<User> users = new ArrayList<>();

}