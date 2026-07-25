package com.medmatch.auth.util;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

import org.springframework.core.io.Resource;

import com.medmatch.auth.exception.BusinessValidationException;

public final class PemUtils {

    private PemUtils() {
    }

    public static RSAPrivateKey readPrivateKey(Resource resource) {
        try {
            String key = readPem(resource);

            key = key
                    .replace("-----BEGIN PRIVATE KEY-----", "")
                    .replace("-----END PRIVATE KEY-----", "")
                    .replaceAll("\\s+", "");

            byte[] decoded = Base64.getDecoder().decode(key);

            PKCS8EncodedKeySpec spec =
                    new PKCS8EncodedKeySpec(decoded);

            KeyFactory keyFactory =
                    KeyFactory.getInstance("RSA");

            return (RSAPrivateKey) keyFactory.generatePrivate(spec);

        } catch (
                IOException |
                NoSuchAlgorithmException |
                InvalidKeySpecException |
                IllegalArgumentException ex
        ) {
            throw new BusinessValidationException(
                    "Failed to load RSA private key from " + resource.getDescription(),
                    ex
            );
        }
    }

    public static RSAPublicKey readPublicKey(Resource resource) {
        try {
            String key = readPem(resource);

            key = key
                    .replace("-----BEGIN PUBLIC KEY-----", "")
                    .replace("-----END PUBLIC KEY-----", "")
                    .replaceAll("\\s+", "");

            byte[] decoded = Base64.getDecoder().decode(key);

            X509EncodedKeySpec spec =
                    new X509EncodedKeySpec(decoded);

            KeyFactory keyFactory =
                    KeyFactory.getInstance("RSA");

            return (RSAPublicKey) keyFactory.generatePublic(spec);

        } catch (
                IOException |
                NoSuchAlgorithmException |
                InvalidKeySpecException |
                IllegalArgumentException ex
        ) {
            throw new BusinessValidationException(
                    "Failed to load RSA public key from " + resource.getDescription(),
                    ex
            );
        }
    }

    private static String readPem(Resource resource) throws IOException {
        return new String(
                resource.getInputStream().readAllBytes(),
                StandardCharsets.UTF_8
        );
    }
}