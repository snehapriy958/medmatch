import time
import uuid
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException

from app.config.security import verify_token
from app.api.deps import get_current_user, get_current_hospital_id


@pytest.fixture
def rsa_keys():
    """Generate ephemeral RSA private and public key pair in PEM format."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


@pytest.fixture
def attacker_rsa_keys():
    """Generate alternate RSA key pair simulating forged signatures."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def test_rsa_jwt_valid_token_e2e(rsa_keys, monkeypatch):
    private_pem, public_pem = rsa_keys
    monkeypatch.setattr("app.config.security.PUBLIC_KEY", public_pem)

    user_id = str(uuid.uuid4())
    hospital_id = str(uuid.uuid4())
    now = int(time.time())

    # Token signed with private key (as Spring Boot auth-service does)
    token = jwt.encode(
        {
            "sub": user_id,
            "email": "dr.priya@testhosp.org",
            "role": "PHYSICIAN",
            "hospital_id": hospital_id,
            "iat": now,
            "exp": now + 3600,
        },
        private_pem,
        algorithm="RS256",
    )

    # Verified by FastAPI security layer
    claims = verify_token(token)
    assert claims["sub"] == user_id
    assert claims["email"] == "dr.priya@testhosp.org"
    assert claims["role"] == "PHYSICIAN"
    assert claims["hospital_id"] == hospital_id

    # Verified by FastAPI dependency injection
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    current_user = get_current_user(creds)
    assert current_user["sub"] == user_id

    extracted_hospital_uuid = get_current_hospital_id(current_user)
    assert str(extracted_hospital_uuid) == hospital_id


def test_rsa_jwt_attacker_signature_rejected(rsa_keys, attacker_rsa_keys, monkeypatch):
    _, legitimate_public_pem = rsa_keys
    attacker_private_pem, _ = attacker_rsa_keys
    monkeypatch.setattr("app.config.security.PUBLIC_KEY", legitimate_public_pem)

    now = int(time.time())
    forged_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "email": "attacker@evil.org",
            "role": "SYSTEM_ADMIN",
            "hospital_id": str(uuid.uuid4()),
            "iat": now,
            "exp": now + 3600,
        },
        attacker_private_pem,
        algorithm="RS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        verify_token(forged_token)

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=forged_token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(creds)
    assert exc_info.value.status_code == 401


def test_rsa_jwt_expired_token_rejected(rsa_keys, monkeypatch):
    private_pem, public_pem = rsa_keys
    monkeypatch.setattr("app.config.security.PUBLIC_KEY", public_pem)

    now = int(time.time())
    expired_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "email": "dr.priya@testhosp.org",
            "role": "PHYSICIAN",
            "hospital_id": str(uuid.uuid4()),
            "iat": now - 7200,
            "exp": now - 3600,
        },
        private_pem,
        algorithm="RS256",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        verify_token(expired_token)


def test_rsa_jwt_missing_required_claims_rejected(rsa_keys, monkeypatch):
    private_pem, public_pem = rsa_keys
    monkeypatch.setattr("app.config.security.PUBLIC_KEY", public_pem)

    now = int(time.time())
    token_missing_hospital = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "email": "dr.priya@testhosp.org",
            "role": "PHYSICIAN",
            # missing hospital_id
            "iat": now,
            "exp": now + 3600,
        },
        private_pem,
        algorithm="RS256",
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        verify_token(token_missing_hospital)
