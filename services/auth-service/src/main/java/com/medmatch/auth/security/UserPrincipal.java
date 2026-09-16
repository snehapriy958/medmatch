package com.medmatch.auth.security;

import java.util.Collection;
import java.util.UUID;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.User;

/**
 * Authentication principal used throughout the request lifecycle.
 *
 * Extends Spring Security's default {@link User} (username = email, so
 * every existing {@code authentication.getName()} call — e.g. in
 * UserServiceImpl's hospital-isolation checks — keeps working unchanged)
 * and additionally carries the user's database id, so callers that need
 * the id (see {@link SecurityUtils#getCurrentUserId()}) don't have to
 * parse it out of the username or make a second repository lookup.
 */
@Getter
public class UserPrincipal extends User {

    private final UUID id;

    public UserPrincipal(
            UUID id,
            String email,
            String password,
            boolean enabled,
            Collection<? extends GrantedAuthority> authorities
    ) {
        super(email, password, enabled, true, true, true, authorities);
        this.id = id;
    }
}
