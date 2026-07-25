package com.medmatch.auth.controller;

import java.util.List;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.medmatch.auth.dto.UserResponse;
import com.medmatch.auth.dto.UserUpdateRequest;
import com.medmatch.auth.service.UserService;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/auth/users")
@PreAuthorize("hasRole('ADMIN')")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    /**
     * Returns all users.
     */
    @GetMapping
    public ResponseEntity<List<UserResponse>> getAllUsers() {

        return ResponseEntity.ok(
                userService.getAllUsers()
        );
    }

    /**
     * Returns a user by ID.
     */
    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUserById(
            @PathVariable UUID id
    ) {

        return ResponseEntity.ok(
                userService.getUserById(id)
        );
    }

    /**
     * Updates an existing user.
     */
    @PutMapping("/{id}")
    public ResponseEntity<UserResponse> updateUser(
            @PathVariable UUID id,
            @Valid @RequestBody UserUpdateRequest request
    ) {

        return ResponseEntity.ok(
                userService.updateUser(id, request)
        );
    }

    /**
     * Deletes a user.
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(
            @PathVariable UUID id
    ) {

        userService.deleteUser(id);

        return ResponseEntity.noContent().build();
    }
}