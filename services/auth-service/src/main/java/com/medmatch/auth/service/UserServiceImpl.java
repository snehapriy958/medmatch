package com.medmatch.auth.service;


import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.User;

import com.medmatch.auth.exception.EmailAlreadyExistsException;
import com.medmatch.auth.exception.ResourceNotFoundException;

import com.medmatch.auth.repository.HospitalRepository;
import com.medmatch.auth.repository.RoleRepository;
import com.medmatch.auth.repository.UserRepository;


import lombok.RequiredArgsConstructor;


import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import org.springframework.security.crypto.password.PasswordEncoder;

import org.springframework.stereotype.Service;

import org.springframework.transaction.annotation.Transactional;


import java.util.List;
import java.util.UUID;



@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {


    private final UserRepository userRepository;

    private final HospitalRepository hospitalRepository;

    private final RoleRepository roleRepository;

    private final PasswordEncoder passwordEncoder;





    @Override
    @Transactional(readOnly = true)
    public UserResponse getUserById(UUID id) {


        User requestedUser =
                userRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "User not found"
                                )
                        );



        Authentication authentication =
                SecurityContextHolder
                        .getContext()
                        .getAuthentication();



        boolean isSystemAdmin =
                authentication.getAuthorities()
                        .stream()
                        .anyMatch(
                                authority ->
                                        authority.getAuthority()
                                                .equals("ROLE_SYSTEM_ADMIN")
                        );



        if (!isSystemAdmin) {


            User currentUser =
                    userRepository.findByEmail(
                            authentication.getName()
                    )
                    .orElseThrow(() ->
                            new ResourceNotFoundException(
                                    "Current user not found"
                            )
                    );



            UUID currentHospitalId =
                    currentUser.getHospital()
                            .getId();



            UUID requestedHospitalId =
                    requestedUser.getHospital()
                            .getId();



            if (!currentHospitalId.equals(requestedHospitalId)) {

                throw new AccessDeniedException(
                        "Cannot access another hospital user"
                );
            }
        }



        return toUserResponse(requestedUser);
    }







    @Override
    @Transactional(readOnly = true)
    public UserResponse getUserByEmail(String email) {


        User user =
                userRepository.findByEmail(email)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "User not found"
                                )
                        );


        return toUserResponse(user);
    }









    @Override
    @Transactional(readOnly = true)
    public List<UserResponse> getUsersByHospital(UUID hospitalId) {


        return userRepository.findByHospitalId(hospitalId)
                .stream()
                .map(this::toUserResponse)
                .toList();
    }









    @Override
    @Transactional
    public UserResponse createUser(RegisterRequest request) {


        if (userRepository.existsByEmail(
                request.getEmail()
        )) {


            throw new EmailAlreadyExistsException(
                    "Email already exists"
            );
        }





        Hospital hospital =
                hospitalRepository.findById(
                        request.getHospitalId()
                )
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






        Role role =
                roleRepository.findByName(
                        request.getRole()
                )
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Role not found"
                        )
                );







        User user =
                User.builder()
                        .email(request.getEmail())
                        .password(
                                passwordEncoder.encode(
                                        request.getPassword()
                                )
                        )
                        .firstName(request.getFirstName())
                        .lastName(request.getLastName())
                        .phone(request.getPhone())
                        .hospital(hospital)
                        .role(role)
                        .enabled(true)
                        .status("ACTIVE")
                        .build();




        User savedUser = userRepository.save(user);

        return toUserResponse(savedUser);
    }









    @Override
    @Transactional
    public void deleteUser(UUID id) {



        User requestedUser =
                userRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "User not found"
                                )
                        );



        Authentication authentication =
                SecurityContextHolder
                        .getContext()
                        .getAuthentication();





        boolean isSystemAdmin =
                authentication.getAuthorities()
                        .stream()
                        .anyMatch(
                                authority ->
                                        authority.getAuthority()
                                                .equals("ROLE_SYSTEM_ADMIN")
                        );





        if (!isSystemAdmin) {



            User currentUser =
                    userRepository.findByEmail(
                            authentication.getName()
                    )
                    .orElseThrow(() ->
                            new ResourceNotFoundException(
                                    "Current user not found"
                            )
                    );



            UUID currentHospitalId =
                    currentUser.getHospital()
                            .getId();



            UUID requestedHospitalId =
                    requestedUser.getHospital()
                            .getId();



            if (!currentHospitalId.equals(requestedHospitalId)) {


                throw new AccessDeniedException(
                        "Cannot delete another hospital user"
                );
            }
        }



        userRepository.delete(requestedUser);
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