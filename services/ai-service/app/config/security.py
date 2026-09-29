import logging
import os
from pathlib import Path
from typing import Any

import jwt

from app.config.settings import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]

def load_public_key() -> str:
    """Load RSA public key with multi-environment fallback.

    Precedence:
    1. JWT_PUBLIC_KEY environment variable (inline PEM string or file path)
    2. JWT_PUBLIC_KEY_PATH environment variable (file path)
    3. services/ai-service/keys/public.pem
    4. services/ai-service/keys/public_key.pem
    5. services/auth-service/src/main/resources/keys/public.pem (monorepo dev fallback)
    6. /app/keys/public.pem (container mount)
    """
    env_key = os.getenv("JWT_PUBLIC_KEY")
    if env_key:
        if os.path.isfile(env_key):
            return Path(env_key).read_text(encoding="utf-8")
        return env_key

    env_path = os.getenv("JWT_PUBLIC_KEY_PATH")
    if env_path and os.path.isfile(env_path):
        return Path(env_path).read_text(encoding="utf-8")

    candidate_paths = [
        BASE_DIR / "keys" / "public.pem",
        BASE_DIR / "keys" / "public_key.pem",
        BASE_DIR.parent / "auth-service" / "src" / "main" / "resources" / "keys" / "public.pem",
        Path("/app/keys/public.pem"),
    ]
    for candidate in candidate_paths:
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding="utf-8")

    raise RuntimeError(
        "RSA public key not found. Configure JWT_PUBLIC_KEY or provide public.pem in keys directory."
    )


PUBLIC_KEY = load_public_key()


def verify_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "require": [
                    "sub",
                    "exp",
                    "iat",
                    "hospital_id",
                    "role",
                ]
            },
        )
    except jwt.InvalidTokenError:
        logger.exception("JWT verification failed")
        raise