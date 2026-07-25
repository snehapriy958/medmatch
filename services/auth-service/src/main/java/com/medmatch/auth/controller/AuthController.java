package com.medmatch.auth.controller;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.medmatch.auth.dto.LoginRequest;
import com.medmatch.auth.dto.LoginResponse;
import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.RegisterResponse;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.service.AuthService;
import com.medmatch.auth.service.UserService;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final UserService userService;
    private final AuthService authService;

    public AuthController(
            UserService userService,
            AuthService authService
    ) {
        this.userService = userService;
        this.authService = authService;
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public RegisterResponse register(
        @Valid @RequestBody RegisterRequest request) {

        User savedUser = userService.register(request);

        return new RegisterResponse(
                savedUser.getId(),
                savedUser.getUsername(),
                savedUser.getEmail(),
                savedUser.getRole()
        );
    }

    @PostMapping("/login")
    public LoginResponse login(
        @Valid @RequestBody LoginRequest request) {

        System.out.println("========== LOGIN CONTROLLER ==========");
        return authService.login(request);
    }
}