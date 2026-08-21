package com.medmatch.auth.service;

import com.medmatch.auth.dto.AuthResponse;
import com.medmatch.auth.dto.LoginRequest;
import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;
import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.EmailAlreadyExistsException;
import com.medmatch.auth.exception.InvalidCredentialsException;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.RoleRepository;
import com.medmatch.auth.repository.UserRepository;
import com.medmatch.auth.security.JwtService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;


@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {


    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final HospitalRepository hospitalRepository;
    private final AuditService auditService;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;


    @Override
    @Transactional
    public UserResponse register(RegisterRequest request) {

        if (userRepository.existsByEmail(request.getEmail())) {

            throw new EmailAlreadyExistsException(
                    "Email already registered"
            );
        }


        Hospital hospital = hospitalRepository.findById(request.getHospitalId())
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Hospital not found"
                        )
                );


        if (!hospital.getActive()) {

            throw new ResourceNotFoundException(
                    "Hospital is inactive"
            );
        }


        Role role = roleRepository.findByName(request.getRole())
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Role not found"
                        )
                );


        User user = User.builder()
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword()))
                .firstName(request.getFirstName())
                .lastName(request.getLastName())
                .phone(request.getPhone())
                .hospital(hospital)
                .role(role)
                .enabled(true)
                .build();


        User savedUser = userRepository.save(user);


        auditService.createAuditLog(
                savedUser.getId(),
                "USER_REGISTERED",
                "USER",
                savedUser.getId(),
                "New user registered: " + savedUser.getEmail()
        );


        return toUserResponse(savedUser);
    }



    @Override
    @Transactional
    public AuthResponse login(LoginRequest request) {


        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> {

                System.out.println(
                        "LOGIN FAILED: USER NOT FOUND = "
                        + request.getEmail()
                );

                return new InvalidCredentialsException(
                        "Invalid email or password"
                );
                });


        System.out.println(
        "LOGIN USER FOUND = "
        + user.getEmail()
        );


        System.out.println(
        "PASSWORD MATCH RESULT = "
        + passwordEncoder.matches(
                request.getPassword(),
                user.getPassword()
        )
        );


                if (!passwordEncoder.matches(
                        request.getPassword(),
                        user.getPassword()
                )) {

                throw new InvalidCredentialsException(
                        "Invalid email or password"
                );
                }

                if (!user.getEnabled()) {

        throw new InvalidCredentialsException(
                        "User account is disabled"
                );
        }


        String token = jwtService.generateToken(user);


        auditService.createAuditLog(
                user.getId(),
                "LOGIN_SUCCESS",
                "USER",
                user.getId(),
                "User logged in: " + user.getEmail()
        );


        return AuthResponse.builder()
                .accessToken(token)
                .tokenType("Bearer")
                .expiresIn(3600000L)
                .user(toUserResponse(user))
                .build();
    }



    private UserResponse toUserResponse(User user) {

        return UserResponse.builder()
                .id(user.getId())
                .firstName(user.getFirstName())
                .lastName(user.getLastName())
                .email(user.getEmail())
                .phone(user.getPhone())
                .role(user.getRole().getName())
                .hospitalId(user.getHospital().getId())
                .status(user.getStatus())
                .enabled(user.getEnabled())
                .build();
    }

}