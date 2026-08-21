package com.medmatch.auth.entity;


import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;


import java.time.LocalDateTime;
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
@Table(name = "users")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {


    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @JdbcTypeCode(SqlTypes.UUID)
    @Column(
            name = "id",
            updatable = false,
            nullable = false
    )
    private UUID id;




    @Column(
            name = "email",
            nullable = false,
            unique = true
    )
    private String email;




    @Column(
            name = "password",
            nullable = false
    )
    private String password;




    @Column(
            name = "first_name",
            nullable = false
    )
    private String firstName;




    @Column(
            name = "last_name",
            nullable = false
    )
    private String lastName;




    @Column(name = "phone")
    private String phone;





    /*
     * User role.
     *
     * Examples:
     * SYSTEM_ADMIN
     * HOSPITAL_ADMIN
     * PHYSICIAN
     * RESEARCH_COORDINATOR
     * TRIAL_SPONSOR
     * PATIENT
     *
     * No cascade intentionally.
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(
            name = "role_id",
            nullable = false
    )
    private Role role;





    /*
     * Tenant boundary.
     *
     * Every user belongs to one hospital.
     *
     * Used for:
     * - hospital isolation
     * - hospital dashboards
     * - RBAC checks
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(
            name = "hospital_id",
            nullable = false
    )
    private Hospital hospital;





    /*
     * Authentication status.
     *
     * enabled:
     * controls login access
     *
     * status:
     * dashboard management state
     *
     * Values:
     * ACTIVE
     * INACTIVE
     * SUSPENDED
     */
    @Builder.Default
    @Column(
            name = "enabled",
            nullable = false
    )
    private Boolean enabled = true;




    @Builder.Default
    @Column(
            name = "status",
            nullable = false
    )
    private String status = "ACTIVE";





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

}