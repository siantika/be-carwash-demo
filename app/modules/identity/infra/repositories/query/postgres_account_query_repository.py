from typing import Any

import asyncpg

from app.modules.identity.application.queries.models import (
    AccountListFilterDto,
)
from app.modules.identity.infra.repositories.account_repo import (
    SELECT_ALL_COLUMNS,
    _mapper,
)
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger


class PostgresAccountQueryRepository:
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def list(
        self,
        *,
        filters: AccountListFilterDto,
        limit: int,
        offset: int,
    ):
        async def _fetch():
            conditions = ["deleted_at IS NULL"]
            params: list[Any] = []

            if filters.role is not None:
                params.append(filters.role.value)
                conditions.append(f"role = ${len(params)}")

            if filters.is_active is not None:
                params.append(filters.is_active)
                conditions.append(f"is_active = ${len(params)}")

            where_clause = " AND ".join(conditions)
            limit_param = len(params) + 1
            offset_param = len(params) + 2

            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM identity.accounts
                WHERE {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT ${limit_param} OFFSET ${offset_param};
                """,
                *params,
                limit,
                offset,
            )
            total = await self.db.fetchval(
                f"""
                SELECT COUNT(*)
                FROM identity.accounts
                WHERE {where_clause};
                """,
                *params,
            )
            return [_mapper(row) for row in rows], int(total or 0)

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={
                "role": filters.role.value if filters.role is not None else None,
                "is_active": filters.is_active,
                "limit": limit,
                "offset": offset,
            },
            operation_name="list identity.accounts",
        )
