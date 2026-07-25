from fastapi import Request
from slowapi import Limiter


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


limiter = Limiter(
    key_func=get_client_ip,
)