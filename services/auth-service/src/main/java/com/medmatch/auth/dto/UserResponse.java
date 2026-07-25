package com.medmatch.auth.dto;

import java.util.UUID;

import com.medmatch.auth.entity.Role;


public class UserResponse {

    private UUID id;

    private String username;

    private String email;

    private Role role;

    private UUID hospitalId;

    private String hospitalCode;

    private String hospitalName;


    public UserResponse() {
    }


    public UserResponse(
            UUID id,
            String username,
            String email,
            Role role,
            UUID hospitalId,
            String hospitalCode,
            String hospitalName
    ) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.role = role;
        this.hospitalId = hospitalId;
        this.hospitalCode = hospitalCode;
        this.hospitalName = hospitalName;
    }


    public UUID getId() {
        return id;
    }


    public void setId(UUID id) {
        this.id = id;
    }


    public String getUsername() {
        return username;
    }


    public void setUsername(String username) {
        this.username = username;
    }


    public String getEmail() {
        return email;
    }


    public void setEmail(String email) {
        this.email = email;
    }


    public Role getRole() {
        return role;
    }


    public void setRole(Role role) {
        this.role = role;
    }


    public UUID getHospitalId() {
        return hospitalId;
    }


    public void setHospitalId(UUID hospitalId) {
        this.hospitalId = hospitalId;
    }


    public String getHospitalCode() {
        return hospitalCode;
    }


    public void setHospitalCode(String hospitalCode) {
        this.hospitalCode = hospitalCode;
    }


    public String getHospitalName() {
        return hospitalName;
    }


    public void setHospitalName(String hospitalName) {
        this.hospitalName = hospitalName;
    }
}