from typing import TypedDict


class JWTClaims(TypedDict, total=False):
    """
    JWT claims issued by Spring Boot Auth Service.
    """

    sub: str
    email: str
    role: str
    hospital_id: int
    iat: int
    exp: int