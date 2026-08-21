package com.medmatch.auth.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.UUID;

public class SecurityUtils {


    public static UUID getCurrentUserId(){

        Authentication authentication =
                SecurityContextHolder
                        .getContext()
                        .getAuthentication();

        return UUID.fromString(
                authentication.getName()
        );
    }
}