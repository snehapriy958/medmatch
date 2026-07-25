from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    status_code: int
    path: str
    request_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Any | None = None