package com.medmatch.auth.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

class SecurityUtilsTest {

    @AfterEach
    void clearContext() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void getCurrentUserId_returnsIdFromUserPrincipal() {
        UUID expectedId = UUID.randomUUID();
        List<GrantedAuthority> authorities = List.of(new SimpleGrantedAuthority("ROLE_PHYSICIAN"));
        UserPrincipal principal = new UserPrincipal(
                expectedId, "dr.priya@testhosp.org", "hashed", true, authorities);

        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(principal, null, authorities));

        assertThat(SecurityUtils.getCurrentUserId()).isEqualTo(expectedId);
    }

    @Test
    void getCurrentUserId_withNoAuthentication_throwsIllegalState() {
        // SecurityContextHolder starts empty (cleared in @AfterEach of the
        // previous test / fresh context per test class instance).
        assertThatThrownBy(SecurityUtils::getCurrentUserId)
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void getCurrentUserId_withNonUserPrincipalAuthentication_throwsIllegalState() {
        // Regression guard: before the fix, this method assumed
        // authentication.getName() was a UUID string and blew up with
        // IllegalArgumentException on a *valid* email-username principal.
        // Now any principal that isn't our UserPrincipal fails loudly and
        // predictably instead.
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("dr.priya@testhosp.org", null, List.of()));

        assertThatThrownBy(SecurityUtils::getCurrentUserId)
                .isInstanceOf(IllegalStateException.class);
    }
}
