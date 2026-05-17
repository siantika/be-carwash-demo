from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class IdempotencyRecord:
    id: int
    scope: str
    idempotency_key: str
    request_hash: str
    status: str
    response_payload: dict[str, Any] | None
    http_status: int | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
