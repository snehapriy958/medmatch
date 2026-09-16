package com.medmatch.auth.security;

import static org.assertj.core.api.Assertions.assertThat;

import com.medmatch.auth.entity.Hospital;
import com.medmatch.auth.entity.Role;
import com.medmatch.auth.entity.RoleType;
import com.medmatch.auth.entity.User;
import com.nimbusds.jwt.SignedJWT;
import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.util.Base64;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * JwtService is constructed and initialized by hand here (no Spring
 * context) so these tests run fast and don't need a database. Each test
 * builds its own RSA key material so signature-tampering scenarios are
 * exercised against genuinely different keys, not mocked booleans.
 */
class JwtServiceTest {

    private User user;

    @BeforeEach
    void setUp() {
        Hospital hospital = Hospital.builder()
                .id(UUID.randomUUID())
                .code("TESTHOSP")
                .name("Test Hospital")
                .active(true)
                .build();

        Role role = Role.builder()
                .id(UUID.randomUUID())
                .name(RoleType.PHYSICIAN)
                .build();

        user = User.builder()
                .id(UUID.randomUUID())
                .email("dr.priya@testhosp.org")
                .password("irrelevant-already-hashed")
                .firstName("Priya")
                .lastName("S")
                .role(role)
                .hospital(hospital)
                .enabled(true)
                .build();
    }

    /** Builds and @PostConstruct-initializes a JwtService against one RSA key pair. */
    private JwtService buildJwtService(KeyPair keyPair, long expirationMillis) throws Exception {
        JwtService jwtService = new JwtService();

        ReflectionTestUtils.setField(jwtService, "privateKeyResource", toPemResource(
                "PRIVATE KEY", keyPair.getPrivate().getEncoded()));
        ReflectionTestUtils.setField(jwtService, "publicKeyResource", toPemResource(
                "PUBLIC KEY", keyPair.getPublic().getEncoded()));
        ReflectionTestUtils.setField(jwtService, "expiration", expirationMillis);

        ReflectionTestUtils.invokeMethod(jwtService, "init");
        return jwtService;
    }

    private Resource toPemResource(String label, byte[] derBytes) {
        String pem = "-----BEGIN " + label + "-----\n"
                + Base64.getEncoder().encodeToString(derBytes)
                + "\n-----END " + label + "-----";
        return new ByteArrayResource(pem.getBytes(StandardCharsets.UTF_8));
    }

    private KeyPair generateRsaKeyPair() throws Exception {
        KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
        generator.initialize(2048);
        return generator.generateKeyPair();
    }

    // --- Core round-trip ---

    @Test
    void generateToken_thenValidate_succeedsForTheSameUser() throws Exception {
        JwtService jwtService = buildJwtService(generateRsaKeyPair(), 3_600_000L);

        String token = jwtService.generateToken(user);
        UserDetails matchingUser = springUser(user.getEmail());

        assertThat(jwtService.validateToken(token, matchingUser)).isTrue();
    }

    @Test
    void generateToken_encodesExpectedClaims() throws Exception {
        JwtService jwtService = buildJwtService(generateRsaKeyPair(), 3_600_000L);

        String token = jwtService.generateToken(user);
        SignedJWT parsed = SignedJWT.parse(token);

        assertThat(parsed.getJWTClaimsSet().getSubject()).isEqualTo(user.getId().toString());
        assertThat(parsed.getJWTClaimsSet().getStringClaim("email")).isEqualTo(user.getEmail());
        assertThat(parsed.getJWTClaimsSet().getStringClaim("role")).isEqualTo("PHYSICIAN");
        assertThat(parsed.getJWTClaimsSet().getStringClaim("hospital_id"))
                .isEqualTo(user.getHospital().getId().toString());
    }

    @Test
    void extractUsername_returnsEmailClaim_notTheSubjectUuid() throws Exception {
        JwtService jwtService = buildJwtService(generateRsaKeyPair(), 3_600_000L);

        String token = jwtService.generateToken(user);

        // Deliberate: extractUsername must return email (what
        // CustomUserDetailsService looks users up by), not the "sub"
        // claim, which holds the UUID. Mixing these up is exactly the
        // kind of bug SecurityUtils had — this test guards against it
        // resurfacing in JwtService itself.
        assertThat(jwtService.extractUsername(token)).isEqualTo(user.getEmail());
        assertThat(jwtService.extractUsername(token)).isNotEqualTo(user.getId().toString());
    }

    // --- Validation failure paths ---

    @Test
    void validateToken_forDifferentUsername_returnsFalse() throws Exception {
        JwtService jwtService = buildJwtService(generateRsaKeyPair(), 3_600_000L);

        String token = jwtService.generateToken(user);
        UserDetails someoneElse = springUser("someone.else@otherhosp.org");

        assertThat(jwtService.validateToken(token, someoneElse)).isFalse();
    }

    @Test
    void validateToken_forExpiredToken_returnsFalse() throws Exception {
        // Negative expiration => expiry timestamp is already in the past
        // the instant the token is minted.
        JwtService jwtService = buildJwtService(generateRsaKeyPair(), -10_000L);

        String token = jwtService.generateToken(user);

        assertThat(jwtService.validateToken(token, springUser(user.getEmail()))).isFalse();
    }

    @Test
    void validateToken_signedByADifferentKeyPair_returnsFalse() throws Exception {
        // Token minted by service A (its own private key)...
        JwtService serviceA = buildJwtService(generateRsaKeyPair(), 3_600_000L);
        String token = serviceA.generateToken(user);

        // ...must not validate against service B, which trusts a
        // completely different key pair. This is the scenario that
        // matters most in production: a forged or replayed token signed
        // with an attacker-controlled key must be rejected.
        JwtService serviceB = buildJwtService(generateRsaKeyPair(), 3_600_000L);

        assertThat(serviceB.validateToken(token, springUser(user.getEmail()))).isFalse();
    }

    @Test
    void validateToken_withTamperedPayload_returnsFalse() throws Exception {
        JwtService jwtService = buildJwtService(generateRsaKeyPair(), 3_600_000L);
        String token = jwtService.generateToken(user);

        // Flip one character in the payload segment (index 1 of the
        // three dot-separated JWT parts) without re-signing — simulates
        // a client trying to smuggle a different role/hospital_id into
        // an otherwise-valid-looking token.
        String[] parts = token.split("\\.");
        char[] payloadChars = parts[1].toCharArray();
        payloadChars[payloadChars.length / 2] =
                payloadChars[payloadChars.length / 2] == 'A' ? 'B' : 'A';
        String tamperedToken = parts[0] + "." + new String(payloadChars) + "." + parts[2];

        assertThat(jwtService.validateToken(tamperedToken, springUser(user.getEmail())))
                .isFalse();
    }

    private UserDetails springUser(String email) {
        return org.springframework.security.core.userdetails.User
                .withUsername(email)
                .password("n/a")
                .authorities("ROLE_PHYSICIAN")
                .build();
    }
}
