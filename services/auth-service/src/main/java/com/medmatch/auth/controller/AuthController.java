package com.medmatch.auth.controller;


import com.medmatch.auth.dto.AuthResponse;
import com.medmatch.auth.dto.LoginRequest;
import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;

import com.medmatch.auth.service.AuthService;

import jakarta.validation.Valid;

import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.security.access.prepost.PreAuthorize;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;



@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {


    private final AuthService authService;




    /*
     * User registration
     *
     * Allowed:
     * - SYSTEM_ADMIN
     * - HOSPITAL_ADMIN
     *
     * Public users cannot create accounts directly.
     *
     * Hospital isolation rules are handled inside service layer.
     */
    @PostMapping("/register")
    @PreAuthorize(
            "hasAnyRole('SYSTEM_ADMIN','HOSPITAL_ADMIN')"
    )
    public ResponseEntity<UserResponse> register(
            @Valid
            @RequestBody RegisterRequest request
    ) {


        UserResponse response =
                authService.register(request);


        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(response);
    }






    /*
     * Login endpoint
     *
     * Returns:
     * - JWT access token
     * - user information
     * - role information
     *
     * Used by frontend authentication flow.
     */
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(
            @Valid
            @RequestBody LoginRequest request
    ) {


        AuthResponse response =
                authService.login(request);


        return ResponseEntity.ok(response);
    }

}