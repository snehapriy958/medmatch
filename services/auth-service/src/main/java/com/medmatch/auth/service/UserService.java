package com.medmatch.auth.service;


import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;


import java.util.List;
import java.util.UUID;



public interface UserService {


    UserResponse getUserById(UUID id);


    List<UserResponse> getUsersByHospital(UUID hospitalId);


    UserResponse createUser(RegisterRequest request);


    UserResponse getUserByEmail(String email);


    void deleteUser(UUID id);

}