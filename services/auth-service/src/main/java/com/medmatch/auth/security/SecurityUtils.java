package com.medmatch.auth.security;

import java.util.UUID;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

import com.medmatch.auth.entity.User;
import com.medmatch.auth.exception.BusinessValidationException;
import com.medmatch.auth.exception.ResourceNotFoundException;
import com.medmatch.auth.repository.UserRepository;


@Component
public class SecurityUtils {

    private final UserRepository userRepository;


    public SecurityUtils(
            UserRepository userRepository
    ) {
        this.userRepository = userRepository;
    }


    /**
     * Returns the currently authenticated user.
     *
     * @throws BusinessValidationException if authentication is missing or invalid.
     * @throws ResourceNotFoundException if the authenticated user no longer exists.
     */
    public User getCurrentUser() {

        Authentication authentication =
                SecurityContextHolder
                        .getContext()
                        .getAuthentication();


        if (authentication == null
                || !authentication.isAuthenticated()
                || "anonymousUser".equals(authentication.getName())) {

            throw new BusinessValidationException(
                    "No authenticated user found."
            );
        }


        try {

            UUID userId = UUID.fromString(
                    authentication.getName()
            );


            return userRepository.findById(userId)
                    .orElseThrow(() ->
                            new ResourceNotFoundException(
                                    "Authenticated user not found."
                            ));


        } catch (IllegalArgumentException ex) {

            throw new BusinessValidationException(
                    "Invalid authenticated user id: "
                            + authentication.getName(),
                    ex
            );
        }
    }
}