from datetime import datetime
from typing import Mapping, Union

import asyncpg

from app.modules.identity.domain.entities.refresh_token import RefreshToken
from app.modules.identity.domain.repositories.i_refresh_token_repo import (
    IRefreshTokenRepository,
)
from app.shared.domain.exceptions.exceptions import RepositoryError
from app.shared.infra.database.error_handler import handle_db_error
from interfaces.i_logger import ILogger

Row = Union[asyncpg.Record, Mapping[str, object]]

SELECT_ALL_COLUMNS = """
id,
account_id,
token_hash,
expires_at,
revoked_at,
last_used_at,
created_at,
updated_at
""".strip()


def _mapper(row: Row) -> RefreshToken:
    if row is None:
        raise RepositoryError("Refresh token row is None")

    return RefreshToken(
        id=row["id"],
        account_id=row["account_id"],
        token_hash=row["token_hash"],
        expires_at=row["expires_at"],
        revoked_at=row["revoked_at"],
        last_used_at=row["last_used_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncPgRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        async def _create():
            row = await self.db.fetchrow(
                f"""
                INSERT INTO identity.refresh_tokens (
                    account_id,
                    token_hash,
                    expires_at,
                    revoked_at,
                    last_used_at
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                refresh_token.account_id,
                refresh_token.token_hash,
                refresh_token.expires_at,
                refresh_token.revoked_at,
                refresh_token.last_used_at,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={"account_id": refresh_token.account_id},
            operation_name="create refresh token",
        )

    async def find_active_by_hash(
        self,
        token_hash: str,
        now: datetime,
    ) -> RefreshToken | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM identity.refresh_tokens
                WHERE token_hash = $1
                  AND revoked_at IS NULL
                  AND expires_at > $2
                LIMIT 1;
                """,
                token_hash,
                now,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={},
            operation_name="fetch active refresh token",
        )

    async def revoke(self, refresh_token_id: int, revoked_at: datetime) -> int:
        async def _update():
            row = await self.db.fetchrow(
                """
                UPDATE identity.refresh_tokens
                SET revoked_at = $2,
                    updated_at = $2
                WHERE id = $1
                RETURNING id;
                """,
                refresh_token_id,
                revoked_at,
            )
            if row is None:
                raise RepositoryError("Refresh token not found")
            return row["id"]

        return await handle_db_error(
            operation=_update,
            logger=self.logger,
            context={"refresh_token_id": refresh_token_id},
            operation_name="revoke refresh token",
        )

    async def mark_used(self, refresh_token_id: int, used_at: datetime) -> int:
        async def _update():
            row = await self.db.fetchrow(
                """
                UPDATE identity.refresh_tokens
                SET last_used_at = $2,
                    updated_at = $2
                WHERE id = $1
                RETURNING id;
                """,
                refresh_token_id,
                used_at,
            )
            if row is None:
                raise RepositoryError("Refresh token not found")
            return row["id"]

        return await handle_db_error(
            operation=_update,
            logger=self.logger,
            context={"refresh_token_id": refresh_token_id},
            operation_name="mark refresh token used",
        )
