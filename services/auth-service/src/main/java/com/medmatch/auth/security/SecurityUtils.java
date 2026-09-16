package com.medmatch.auth.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.UUID;

public class SecurityUtils {

    /**
     * Returns the id of the currently authenticated user.
     *
     * NOTE: previously this parsed {@code authentication.getName()} as a
     * UUID. That name is the user's *email* (see JwtService#extractUsername
     * and CustomUserDetailsService), not the id, so the old implementation
     * threw IllegalArgumentException on every call. It was unused in the
     * codebase so the bug was latent. Fixed to read the id off the
     * UserPrincipal set by CustomUserDetailsService.
     */
    public static UUID getCurrentUserId() {

        Authentication authentication =
                SecurityContextHolder
                        .getContext()
                        .getAuthentication();

        if (authentication == null
                || !(authentication.getPrincipal() instanceof UserPrincipal principal)) {

            throw new IllegalStateException(
                    "No authenticated UserPrincipal in the current security context"
            );
        }

        return principal.getId();
    }
}