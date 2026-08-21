package com.medmatch.auth.security;

import jakarta.annotation.Nonnull;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;

import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;

import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

@Component
@RequiredArgsConstructor
@Slf4j
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String AUTH_HEADER = "Authorization";

    private static final String BEARER_PREFIX = "Bearer ";

    private static final List<String> PUBLIC_PATHS = List.of(
            "/auth/login",
            "/api/auth/login",
            "/health",
            "/actuator",
            "/swagger-ui",
            "/swagger-ui.html",
            "/v3/api-docs"
    );

    private final JwtService jwtService;

    private final CustomUserDetailsService userDetailsService;

    @Override
    protected boolean shouldNotFilter(
            @Nonnull HttpServletRequest request
    ) {

        String path = request.getRequestURI();

        return PUBLIC_PATHS.stream()
                .anyMatch(path::startsWith);
    }

    @Override
    protected void doFilterInternal(
            @Nonnull HttpServletRequest request,
            @Nonnull HttpServletResponse response,
            @Nonnull FilterChain filterChain
    ) throws ServletException, IOException {

        String requestUri = request.getRequestURI();

        String authHeader = request.getHeader(AUTH_HEADER);

        if (authHeader == null || !authHeader.startsWith(BEARER_PREFIX)) {

            log.debug(
                    "JWT authentication skipped: no Bearer token for {}",
                    requestUri
            );

            filterChain.doFilter(request, response);

            return;
        }

        String token = authHeader.substring(
                BEARER_PREFIX.length()
        );

        try {

            String username = jwtService.extractUsername(token);

            log.debug(
                    "JWT username extracted for {}: {}",
                    requestUri,
                    username
            );

            if (username != null &&
                    SecurityContextHolder
                            .getContext()
                            .getAuthentication() == null) {

                UserDetails userDetails =
                        userDetailsService.loadUserByUsername(username);

                boolean valid =
                        jwtService.validateToken(
                                token,
                                userDetails
                        );

                log.debug(
                        "JWT validation result for {}: {}",
                        requestUri,
                        valid
                );

                if (valid) {

                    UsernamePasswordAuthenticationToken authToken =
                            new UsernamePasswordAuthenticationToken(
                                    userDetails,
                                    null,
                                    userDetails.getAuthorities()
                            );

                    authToken.setDetails(
                            new WebAuthenticationDetailsSource()
                                    .buildDetails(request)
                    );

                    SecurityContextHolder
                            .getContext()
                            .setAuthentication(authToken);

                    log.debug(
                            "JWT authentication established for {} as {} with authorities {}",
                            requestUri,
                            username,
                            userDetails.getAuthorities()
                    );
                } else {

                    log.warn(
                            "JWT validation failed for {}",
                            requestUri
                    );
                }
            }

        } catch (Exception ex) {

            log.error(
                    "JWT authentication failed for {}: {}",
                    requestUri,
                    ex.getMessage(),
                    ex
            );

            SecurityContextHolder.clearContext();
        }

        filterChain.doFilter(request, response);
    }
}