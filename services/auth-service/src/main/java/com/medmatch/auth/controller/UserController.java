package com.medmatch.auth.controller;


import com.medmatch.auth.dto.RegisterRequest;
import com.medmatch.auth.dto.UserResponse;
import com.medmatch.auth.service.UserService;


import jakarta.validation.Valid;


import lombok.RequiredArgsConstructor;


import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;


import org.springframework.security.access.prepost.PreAuthorize;


import org.springframework.web.bind.annotation.*;


import java.security.Principal;
import java.util.List;
import java.util.UUID;



@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {


    private final UserService userService;





    /*
     * Current logged-in user
     *
     * Dashboard usage:
     * - profile details
     * - role information
     * - hospital information
     */
    @GetMapping("/me")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<UserResponse> getCurrentUser(
            Principal principal
    ){

        return ResponseEntity.ok(
                userService.getUserByEmail(
                        principal.getName()
                )
        );
    }






    /*
     * Create new user
     *
     * Used by:
     * - SYSTEM_ADMIN
     * - HOSPITAL_ADMIN
     *
     * Examples:
     * - Add doctor
     * - Add researcher
     * - Add patient
     */
    @PostMapping
    @PreAuthorize(
            "hasAnyRole('SYSTEM_ADMIN','HOSPITAL_ADMIN')"
    )
    public ResponseEntity<UserResponse> createUser(
            @Valid
            @RequestBody RegisterRequest request
    ){

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(
                        userService.createUser(request)
                );
    }








    /*
     * Get user by id
     *
     * SYSTEM_ADMIN:
     *      access all hospitals
     *
     * HOSPITAL_ADMIN:
     *      own hospital users only
     */
    @GetMapping("/{id}")
    @PreAuthorize(
            "hasAnyRole('SYSTEM_ADMIN','HOSPITAL_ADMIN')"
    )
    public ResponseEntity<UserResponse> getUserById(
            @PathVariable UUID id
    ){

        return ResponseEntity.ok(
                userService.getUserById(id)
        );
    }









    /*
     * Hospital user management
     *
     * Dashboard usage:
     * - Doctors list
     * - Researchers list
     * - Patients list
     */
    @GetMapping("/hospital/{hospitalId}")
    @PreAuthorize(
            "hasAnyRole('SYSTEM_ADMIN','HOSPITAL_ADMIN')"
    )
    public ResponseEntity<List<UserResponse>> getUsersByHospital(
            @PathVariable UUID hospitalId
    ){

        return ResponseEntity.ok(
                userService.getUsersByHospital(
                        hospitalId
                )
        );
    }









    /*
     * Delete user
     *
     * Permission:
     * - SYSTEM_ADMIN
     * - HOSPITAL_ADMIN
     *
     * Hospital isolation:
     * handled inside UserService
     */
    @DeleteMapping("/{id}")
    @PreAuthorize(
            "hasAnyRole('SYSTEM_ADMIN','HOSPITAL_ADMIN')"
    )
    public ResponseEntity<Void> deleteUser(
            @PathVariable UUID id
    ){

        userService.deleteUser(id);


        return ResponseEntity
                .noContent()
                .build();
    }

}