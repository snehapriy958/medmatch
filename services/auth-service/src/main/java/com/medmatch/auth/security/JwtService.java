package com.medmatch.auth.security;

import com.medmatch.auth.entity.User;
import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.RSASSASigner;
import com.nimbusds.jose.crypto.RSASSAVerifier;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import jakarta.annotation.PostConstruct;
import java.security.KeyFactory;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.text.ParseException;
import java.util.Base64;
import java.util.Date;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.core.io.Resource;
import java.nio.charset.StandardCharsets;

@Service
public class JwtService {

    // Bound via Spring's relaxed env-var binding: the Kubernetes Secret
    // keys JWT_PRIVATE_KEY / JWT_PUBLIC_KEY map to jwt.private-key /
    // jwt.public-key automatically, no application.yml entry required.
    @Value("${jwt.private-key}")
    private Resource privateKeyResource;

    @Value("${jwt.public-key}")
    private Resource publicKeyResource;

    @Value("${jwt.expiration}")
    private long expiration;

    private RSASSASigner signer;
    private RSASSAVerifier verifier;

    @PostConstruct
    public void init() throws Exception {

        String privateKey =
                new String(
                        privateKeyResource.getInputStream().readAllBytes(),
                        StandardCharsets.UTF_8
                );

        String publicKey =
                new String(
                        publicKeyResource.getInputStream().readAllBytes(),
                        StandardCharsets.UTF_8
                );

        RSAPrivateKey rsaPrivateKey =
                parsePrivateKey(privateKey);

        RSAPublicKey rsaPublicKey =
                parsePublicKey(publicKey);

        this.signer = new RSASSASigner(rsaPrivateKey);
        this.verifier = new RSASSAVerifier(rsaPublicKey);
    }

    public String generateToken(User user) {
        try {
            Date now = new Date();
            Date expiry = new Date(now.getTime() + expiration);

            JWTClaimsSet claims = new JWTClaimsSet.Builder()
                    .subject(user.getId().toString())
                    .claim("email", user.getEmail())
                    .claim("role", user.getRole().getName().name())
                    .claim("hospital_id", user.getHospital().getId().toString())
                    .issueTime(now)
                    .expirationTime(expiry)
                    .build();

            SignedJWT signedJWT = new SignedJWT(new JWSHeader(JWSAlgorithm.RS256), claims);
            signedJWT.sign(signer);
            return signedJWT.serialize();
        } catch (JOSEException e) {
            throw new IllegalStateException("Failed to generate JWT", e);
        }
    }

    // Returns the "email" claim, not "sub" — "sub" holds the user's UUID
    // (see generateToken above), while Spring Security's UserDetails
    // treats email as the username. This method's return value is what
    // JwtAuthenticationFilter passes to CustomUserDetailsService.
    public String extractUsername(String token) {
        try {
            SignedJWT signedJWT = SignedJWT.parse(token);
            return signedJWT.getJWTClaimsSet().getStringClaim("email");
        } catch (ParseException e) {
            throw new IllegalStateException("Failed to parse JWT", e);
        }
    }

    public boolean validateToken(String token, UserDetails userDetails) {
        try {
            SignedJWT signedJWT = SignedJWT.parse(token);

            if (!signedJWT.verify(verifier)) {
                return false;
            }

            Date expiration = signedJWT.getJWTClaimsSet().getExpirationTime();
            if (expiration == null || expiration.before(new Date())) {
                return false;
            }

            String email = signedJWT.getJWTClaimsSet().getStringClaim("email");
            return email != null && email.equals(userDetails.getUsername());
        } catch (ParseException | JOSEException e) {
            return false;
        }
    }

    private RSAPrivateKey parsePrivateKey(String pem) throws Exception {
        String cleaned = pem
                .replace("-----BEGIN PRIVATE KEY-----", "")
                .replace("-----END PRIVATE KEY-----", "")
                .replaceAll("\\s", "");
        byte[] decoded = Base64.getDecoder().decode(cleaned);
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        return (RSAPrivateKey) keyFactory.generatePrivate(new PKCS8EncodedKeySpec(decoded));
    }

    private RSAPublicKey parsePublicKey(String pem) throws Exception {
        String cleaned = pem
                .replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", "");
        byte[] decoded = Base64.getDecoder().decode(cleaned);
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        return (RSAPublicKey) keyFactory.generatePublic(new X509EncodedKeySpec(decoded));
    }
}