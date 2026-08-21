package com.medmatch.auth.service;

import com.medmatch.auth.dto.AuthResponse;
import com.medmatch.auth.dto.LoginRequest;
import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;

public interface AuthService {

    UserResponse register(RegisterRequest request);

    AuthResponse login(LoginRequest request);
}
