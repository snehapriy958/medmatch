package com.medmatch.auth.dto;


import com.medmatch.auth.entity.RoleType;


import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;


import java.util.UUID;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;



@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RegisterRequest {


    @NotBlank(
            message = "First name is required"
    )
    private String firstName;



    @NotBlank(
            message = "Last name is required"
    )
    private String lastName;



    @NotBlank(
            message = "Email is required"
    )
    @Email(
            message = "Invalid email format"
    )
    private String email;



    @NotBlank(
            message = "Password is required"
    )
    @Size(
            min = 8,
            message = "Password must contain at least 8 characters"
    )
    private String password;



    private String phone;




    /*
     * Hospital tenant.
     *
     * Every user must belong to a hospital.
     */
    @NotNull(
            message = "Hospital id is required"
    )
    private UUID hospitalId;




    /*
     * Assigned role.
     *
     * Current supported roles:
     *
     * SYSTEM_ADMIN
     * HOSPITAL_ADMIN
     * PHYSICIAN
     * RESEARCH_COORDINATOR
     * TRIAL_SPONSOR
     * PATIENT
     *
     * Role assignment restrictions
     * will be enforced in service layer.
     */
    @NotNull(
            message = "Role is required"
    )
    private RoleType role;

}