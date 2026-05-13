import json
from datetime import datetime
from typing import Any, Mapping

import asyncpg

from app.modules.billing.domain.entities.idempotency_record import IdempotencyRecord
from app.modules.billing.domain.repositories.i_idempotency_repo import IIdempotencyRepository
from app.shared.domain.exceptions.exceptions import EntityAlreadyExists, RepositoryError
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger

Row = asyncpg.Record | Mapping[str, Any]

SELECT_ALL_COLUMNS = """
id,
scope,
idempotency_key,
request_hash,
status,
response_payload,
http_status,
created_at,
updated_at,
expires_at
""".strip()


def _mapper(row: Row) -> IdempotencyRecord:
    if row is None:
        raise RepositoryError("Idempotency row is None")
    data = dict(row) if not isinstance(row, dict) else row
    payload = data.get("response_payload")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = None
    elif payload is not None and not isinstance(payload, dict):
        payload = None
    return IdempotencyRecord(
        id=data["id"],
        scope=data["scope"],
        idempotency_key=data["idempotency_key"],
        request_hash=data["request_hash"],
        status=data["status"],
        response_payload=payload,
        http_status=data["http_status"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        expires_at=data["expires_at"],
    )


class AsyncPgIdempotencyRepository(IIdempotencyRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def find_by_scope_and_key(
        self,
        *,
        scope: str,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM billing.idempotency_keys
                WHERE scope = $1 AND idempotency_key = $2;
                """,
                scope,
                idempotency_key,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"scope": scope, "idempotency_key": idempotency_key},
            operation_name="fetch idempotency key",
        )

    async def create_processing(
        self,
        *,
        scope: str,
        idempotency_key: str,
        request_hash: str,
        expires_at: datetime,
    ) -> IdempotencyRecord:
        async def _create():
            try:
                row = await self.db.fetchrow(
                    f"""
                    INSERT INTO billing.idempotency_keys (
                        scope,
                        idempotency_key,
                        request_hash,
                        status,
                        expires_at
                    )
                    VALUES ($1, $2, $3, 'PROCESSING', $4)
                    RETURNING {SELECT_ALL_COLUMNS};
                    """,
                    scope,
                    idempotency_key,
                    request_hash,
                    expires_at,
                )
            except asyncpg.UniqueViolationError as exc:
                raise EntityAlreadyExists("IdempotencyKey", idempotency_key) from exc
            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={"scope": scope, "idempotency_key": idempotency_key},
            operation_name="create idempotency key",
        )

    async def mark_completed(
        self,
        *,
        record_id: int,
        response_payload: dict,
        http_status: int,
    ) -> IdempotencyRecord:
        async def _update():
            row = await self.db.fetchrow(
                f"""
                UPDATE billing.idempotency_keys
                SET
                    status = 'COMPLETED',
                    response_payload = $2::jsonb,
                    http_status = $3,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                record_id,
                json.dumps(response_payload),
                http_status,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_update,
            logger=self.logger,
            context={"record_id": record_id},
            operation_name="mark idempotency completed",
        )
