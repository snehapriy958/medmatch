# from pathlib import Path
# from typing import Any

# import jwt

# from app.config.settings import settings


# BASE_DIR = Path(__file__).resolve().parents[2]

# PUBLIC_KEY_PATH = (
#     BASE_DIR
#     / "keys"
#     / "public_key.pem"
# )

# PUBLIC_KEY = PUBLIC_KEY_PATH.read_text(
#     encoding="utf-8",
# )


# def verify_token(token: str) -> dict[str, Any]:
#     """
#     Verify an RS256 JWT issued by the Spring Boot Auth Service.
#     """

#     return jwt.decode(
#         token,
#         PUBLIC_KEY,
#         algorithms=[settings.JWT_ALGORITHM],
#         options={
#             "require": [
#                 "sub",
#                 "exp",
#                 "iat",
#                 "hospital_id",
#                 "role",
#             ]
#         },
#     )


from pathlib import Path
from typing import Any
import logging
import jwt

from app.config.settings import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]

PUBLIC_KEY_PATH = BASE_DIR / "keys" / "public_key.pem"

PUBLIC_KEY = PUBLIC_KEY_PATH.read_text(encoding="utf-8")


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