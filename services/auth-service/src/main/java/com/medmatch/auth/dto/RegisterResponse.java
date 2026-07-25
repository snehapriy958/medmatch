package com.medmatch.auth.dto;

import java.util.UUID;

import com.medmatch.auth.entity.Role;


public class RegisterResponse {

    private UUID id;

    private String username;

    private String email;

    private Role role;


    public RegisterResponse() {
    }


    public RegisterResponse(
            UUID id,
            String username,
            String email,
            Role role
    ) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.role = role;
    }


    public UUID getId() {
        return id;
    }


    public String getUsername() {
        return username;
    }


    public String getEmail() {
        return email;
    }


    public Role getRole() {
        return role;
    }
}