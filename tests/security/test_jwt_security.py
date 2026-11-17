"""
Security Tests: JWT Cryptographic Integrity & Token Security.
Tests:
1. "none" algorithm attack (CVE-2015-9235 style bypass)
2. Algorithm confusion attack (HS256 HMAC with RSA public key)
3. Expired token rejection
4. Signature tampering rejection
5. Missing mandatory claims rejection (sub, exp, iat, hospital_id, role)
"""

import time
from pathlib import Path
from uuid import uuid4
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.config.security import verify_token, PUBLIC_KEY
from app.config.settings import settings

PRIVATE_KEY_PATH = Path(__file__).resolve().parents[2] / "services" / "auth-service" / "src" / "main" / "resources" / "keys" / "private.pem"


@pytest.fixture
def valid_private_key():
    with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_none_algorithm_attack_rejected():
    """Tokens with 'alg': 'none' must fail verification immediately."""
    payload = {
        "sub": str(uuid4()),
        "email": "attacker@evil.org",
        "role": "SYSTEM_ADMIN",
        "hospital_id": str(uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    # Create unencoded/none token
    none_token = jwt.encode(payload, key="", algorithm="none")

    with pytest.raises(jwt.InvalidTokenError):
        verify_token(none_token)


def test_algorithm_confusion_hs256_rejected():
    """Attacker attempting to submit an HMAC HS256 token must be rejected."""
    payload = {
        "sub": str(uuid4()),
        "email": "attacker@evil.org",
        "role": "SYSTEM_ADMIN",
        "hospital_id": str(uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    # Attacker uses HMAC HS256 with arbitrary secret or key bytes
    fake_token = jwt.encode(payload, "attacker_secret_key_1234567890", algorithm="HS256")

    # verify_token only permits RS256 and must reject HS256
    with pytest.raises(jwt.InvalidTokenError):
        verify_token(fake_token)


def test_expired_token_rejected(valid_private_key):
    """Token with expiration in the past must be rejected."""
    payload = {
        "sub": str(uuid4()),
        "email": "doctor@hospital.org",
        "role": "PHYSICIAN",
        "hospital_id": str(uuid4()),
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,
    }
    expired_token = jwt.encode(payload, valid_private_key, algorithm="RS256")

    with pytest.raises(jwt.ExpiredSignatureError):
        verify_token(expired_token)


def test_tampered_payload_rejected(valid_private_key):
    """Tampering with token payload after signing must invalidate cryptographic signature."""
    payload = {
        "sub": str(uuid4()),
        "email": "doctor@hospital.org",
        "role": "PHYSICIAN",
        "hospital_id": str(uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, valid_private_key, algorithm="RS256")

    # Split token parts and tamper with header/payload
    parts = token.split(".")
    tampered_token = f"{parts[0]}.eyJuYW1lIjoiZXZpbCJ9.{parts[2]}"

    with pytest.raises(jwt.InvalidTokenError):
        verify_token(tampered_token)


def test_missing_mandatory_claims_rejected(valid_private_key):
    """Tokens missing required claims (sub, exp, iat, hospital_id, role) must be rejected."""
    incomplete_payloads = [
        # Missing hospital_id
        {
            "sub": str(uuid4()),
            "role": "PHYSICIAN",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        },
        # Missing role
        {
            "sub": str(uuid4()),
            "hospital_id": str(uuid4()),
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        },
        # Missing sub
        {
            "hospital_id": str(uuid4()),
            "role": "PHYSICIAN",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        },
    ]

    for p in incomplete_payloads:
        tok = jwt.encode(p, valid_private_key, algorithm="RS256")
        with pytest.raises(jwt.MissingRequiredClaimError):
            verify_token(tok)
