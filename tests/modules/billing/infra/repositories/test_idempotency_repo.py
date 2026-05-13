from datetime import timedelta

import pytest

from app.modules.billing.infra.repositories.idempotency_repo import (
    AsyncPgIdempotencyRepository,
)
from app.shared.domain.entities.base import _utcnow


class FakeLogger:
    def info(self, event: str, **kwargs):
        return None

    def error(self, event: str, **kwargs):
        return None

    def warning(self, event: str, **kwargs):
        return None

    def debug(self, event: str, **kwargs):
        return None


class FakeDb:
    def __init__(self):
        self.rows: dict[tuple[str, str], dict] = {}
        self.next_id = 1

    async def fetchrow(self, query: str, *args):
        normalized = " ".join(query.split())
        if "INSERT INTO billing.idempotency_keys" in normalized:
            scope, key, request_hash, expires_at = args
            row_key = (scope, key)
            if row_key in self.rows:
                import asyncpg

                raise asyncpg.UniqueViolationError("duplicate key")
            now = _utcnow()
            row = {
                "id": self.next_id,
                "scope": scope,
                "idempotency_key": key,
                "request_hash": request_hash,
                "status": "PROCESSING",
                "response_payload": None,
                "http_status": None,
                "created_at": now,
                "updated_at": now,
                "expires_at": expires_at,
            }
            self.next_id += 1
            self.rows[row_key] = row
            return row

        if "FROM billing.idempotency_keys WHERE scope = $1 AND idempotency_key = $2" in normalized:
            scope, key = args
            return self.rows.get((scope, key))

        if "UPDATE billing.idempotency_keys SET status = 'COMPLETED'" in normalized:
            record_id, response_payload, http_status = args
            for row in self.rows.values():
                if row["id"] == record_id:
                    row["status"] = "COMPLETED"
                    row["response_payload"] = response_payload
                    row["http_status"] = http_status
                    row["updated_at"] = _utcnow()
                    return row
            return None

        return None


@pytest.mark.anyio
async def test_create_find_and_mark_completed_idempotency_record() -> None:
    db = FakeDb()
    repo = AsyncPgIdempotencyRepository(db, FakeLogger())

    created = await repo.create_processing(
        scope="process_transaction",
        idempotency_key="abc12345",
        request_hash="hash-1",
        expires_at=_utcnow() + timedelta(hours=24),
    )
    assert created.status == "PROCESSING"

    found = await repo.find_by_scope_and_key(
        scope="process_transaction",
        idempotency_key="abc12345",
    )
    assert found is not None
    assert found.request_hash == "hash-1"

    completed = await repo.mark_completed(
        record_id=created.id,
        response_payload={"id": 99, "ticket_id": 1},
        http_status=201,
    )
    assert completed.status == "COMPLETED"
    assert completed.response_payload is not None
    assert completed.response_payload["id"] == 99

