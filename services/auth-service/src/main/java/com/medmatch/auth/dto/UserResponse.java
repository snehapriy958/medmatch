package com.medmatch.auth.dto;


import com.medmatch.auth.entity.RoleType;

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
public class UserResponse {


    private UUID id;


    private String firstName;


    private String lastName;


    private String email;


    private String phone;


    private RoleType role;


    private UUID hospitalId;



    /*
     * User lifecycle status.
     *
     * Values:
     * ACTIVE
     * INACTIVE
     * SUSPENDED
     *
     * Used by admin dashboards.
     */
    private String status;



    /*
     * Authentication availability.
     *
     * true  -> can login
     * false -> blocked
     */
    private Boolean enabled;

}