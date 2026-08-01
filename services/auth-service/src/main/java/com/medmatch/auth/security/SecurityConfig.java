package com.medmatch.auth.security;

import java.util.List;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    private final Converter<Jwt, AbstractAuthenticationToken> jwtAuthenticationConverter;

    public SecurityConfig(
            Converter<Jwt, AbstractAuthenticationToken> jwtAuthenticationConverter
    ) {
        this.jwtAuthenticationConverter = jwtAuthenticationConverter;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http)
            throws Exception {

        http
                .csrf(csrf -> csrf.disable())
                .cors(Customizer.withDefaults())

                .authorizeHttpRequests(auth -> auth

                        // ---------- Public ----------
                        .requestMatchers(
                                "/health",
                                "/health/**",
                                "/auth/login",
                                "/swagger-ui/**",
                                "/swagger-ui.html",
                                "/v3/api-docs/**"
                        ).permitAll()

                        .requestMatchers(
                                "/actuator/health",
                                "/actuator/health/**",
                                "/actuator/info",
                                "/actuator/prometheus"
                        ).permitAll()


                        // ---------- ADMIN ----------
                        .requestMatchers(
                                "/auth/register",
                                "/auth/hospitals/**",
                                "/auth/users/**",
                                "/auth/audit-logs/**"
                        ).hasRole("ADMIN")

                        // ---------- ADMIN + RESEARCHER ----------
                        .requestMatchers(
                                "/api/trials/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "RESEARCHER"
                        )
                        

                        // ---------- ADMIN + DOCTOR + RESEARCHER ----------
                        .requestMatchers(
                                "/auth/dashboard/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "DOCTOR",
                                "RESEARCHER"
                        )
                        

                        // ---------- ADMIN + DOCTOR ----------
                        .requestMatchers(
                                "/auth/patients/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "DOCTOR"
                        )

                        // ---------- DOCTOR + RESEARCHER ----------
                        .requestMatchers(
                                "/matching/search"
                        ).hasAnyRole(
                                "DOCTOR",
                                "RESEARCHER"
                        )

                        // ---------- DOCTOR ----------
                        .requestMatchers(
                                "/matching/evaluate"
                        ).hasRole("DOCTOR")

                        .anyRequest().authenticated()
                )

                .oauth2ResourceServer(oauth2 ->
                        oauth2.jwt(jwt ->
                                jwt.jwtAuthenticationConverter(jwtAuthenticationConverter)
                        )
                );

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {

        CorsConfiguration configuration = new CorsConfiguration();

        configuration.setAllowedOriginPatterns(List.of(
                "http://localhost:*",
                "http://127.0.0.1:*",
                "http://medmatch.local:*"
        ));

        configuration.setAllowedMethods(List.of(
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS"
        ));

        configuration.setAllowedHeaders(List.of("*"));

        configuration.setExposedHeaders(List.of(
                "Authorization"
        ));

        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source =
                new UrlBasedCorsConfigurationSource();

        source.registerCorsConfiguration("/**", configuration);

        return source;
    }
}