from datetime import datetime
from typing import Protocol

from app.modules.billing.domain.entities.idempotency_record import IdempotencyRecord


class IIdempotencyRepository(Protocol):
    async def find_by_scope_and_key(
        self,
        *,
        scope: str,
        idempotency_key: str,
    ) -> IdempotencyRecord | None: ...

    async def create_processing(
        self,
        *,
        scope: str,
        idempotency_key: str,
        request_hash: str,
        expires_at: datetime,
    ) -> IdempotencyRecord: ...

    async def mark_completed(
        self,
        *,
        record_id: int,
        response_payload: dict,
        http_status: int,
    ) -> IdempotencyRecord: ...

