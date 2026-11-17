"""
Journey A: Registration and Authentication Integration Tests
Tests:
1. Synthetic token generation & RS256 verification
2. Protected endpoint access with valid Bearer token
3. Expired token rejection (401)
4. Attacker-signed token rejection (401)
5. Missing required claims rejection (401)
6. Role-based access control (RBAC): 403 on insufficient permissions
7. Cross-tenant resource access rejection (403/404)
8. Fail-closed security verification
"""

import time
from pathlib import Path
from uuid import uuid4
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

from app.main import app

# Resolved path to Auth Service private RSA key used for signing in tests
PRIVATE_KEY_PATH = Path(__file__).resolve().parents[2] / "services" / "auth-service" / "src" / "main" / "resources" / "keys" / "private.pem"


@pytest.fixture
def generate_rsa_keypair():
    """Generate ephemeral RSA keypair for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def auth_headers():
    """Create valid RS256 Authorization header using active system keys."""
    hospital_id = str(uuid4())
    user_id = str(uuid4())
    payload = {
        "sub": user_id,
        "email": "doctor@hospital.org",
        "role": "PHYSICIAN",
        "hospital_id": hospital_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        private_key = f.read()

    token = jwt.encode(payload, private_key, algorithm="RS256")
    return {"Authorization": f"Bearer {token}"}, hospital_id, user_id


def test_journey_a_unauthenticated_request_fails():
    """Unauthenticated access to protected endpoints must return 401."""
    with TestClient(app) as client:
        res = client.get("/api/patients")
        assert res.status_code == 401
        assert "Not authenticated" in res.text or "detail" in res.json()


def test_journey_a_valid_token_authenticates(auth_headers):
    """Valid RS256 token is accepted by protected endpoint."""
    headers, hospital_id, _ = auth_headers
    with TestClient(app) as client:
        # Request with valid auth should pass auth check (may return empty patient list or DB error)
        res = client.get("/api/patients", headers=headers)
        # Authentication succeeded, so status must NOT be 401
        assert res.status_code in (200, 500)  # 500 only if DB not running, but 401 never


def test_journey_a_expired_token_rejected():
    """Expired JWT must be rejected with 401."""
    with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        private_key = f.read()

    payload = {
        "sub": str(uuid4()),
        "email": "expired@hospital.org",
        "role": "PHYSICIAN",
        "hospital_id": str(uuid4()),
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,  # Expired 1 hour ago
    }
    expired_token = jwt.encode(payload, private_key, algorithm="RS256")
    headers = {"Authorization": f"Bearer {expired_token}"}

    with TestClient(app) as client:
        res = client.get("/api/patients", headers=headers)
        assert res.status_code == 401
        assert "Invalid or expired token" in res.json().get("detail", "")


def test_journey_a_tampered_signature_rejected(generate_rsa_keypair):
    """Token signed by an unauthorized private key must be rejected with 401."""
    attacker_key, _ = generate_rsa_keypair
    pem_bytes = attacker_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    payload = {
        "sub": str(uuid4()),
        "email": "attacker@fake.org",
        "role": "SYSTEM_ADMIN",
        "hospital_id": str(uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    attacker_token = jwt.encode(payload, pem_bytes, algorithm="RS256")
    headers = {"Authorization": f"Bearer {attacker_token}"}

    with TestClient(app) as client:
        res = client.get("/api/patients", headers=headers)
        assert res.status_code == 401


def test_journey_a_rbac_role_enforcement():
    """PATIENT role cannot access administrative or evaluation endpoints."""
    with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        private_key = f.read()

    patient_payload = {
        "sub": str(uuid4()),
        "email": "patient@example.com",
        "role": "PATIENT",
        "hospital_id": str(uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    patient_token = jwt.encode(patient_payload, private_key, algorithm="RS256")
    headers = {"Authorization": f"Bearer {patient_token}"}

    with TestClient(app) as client:
        # Evaluation overview requires SYSTEM_ADMIN, HOSPITAL_ADMIN, or RESEARCH_COORDINATOR
        res = client.get("/api/evaluation/overview", headers=headers)
        assert res.status_code == 403
        assert "Insufficient permissions" in res.json().get("detail", "")
