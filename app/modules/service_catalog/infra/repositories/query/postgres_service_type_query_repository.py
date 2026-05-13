from typing import Any

import asyncpg

from app.modules.service_catalog.application.queries.models import (
    ServiceTypeListFilterDto,
)
from app.modules.service_catalog.infra.repositories.service_type_repo import (
    SELECT_ALL_COLUMNS,
    _mapper,
)
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger


class PostgresServiceTypeQueryRepository:
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def list(
        self,
        *,
        filters: ServiceTypeListFilterDto,
        limit: int,
        offset: int,
    ):
        async def _fetch():
            conditions = ["deleted_at IS NULL"]
            params: list[Any] = []

            if filters.q is not None:
                params.append(f"%{filters.q}%")
                conditions.append(
                    f"(name ILIKE ${len(params)} OR description ILIKE ${len(params)})"
                )

            if filters.is_active is not None:
                params.append(filters.is_active)
                conditions.append(f"is_active = ${len(params)}")

            if filters.is_primary is not None:
                params.append(filters.is_primary)
                conditions.append(f"is_primary = ${len(params)}")

            if filters.min_price is not None:
                params.append(filters.min_price)
                conditions.append(f"price >= ${len(params)}")

            if filters.max_price is not None:
                params.append(filters.max_price)
                conditions.append(f"price <= ${len(params)}")

            where_clause = " AND ".join(conditions)
            limit_param = len(params) + 1
            offset_param = len(params) + 2

            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM service_catalog.service_types
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
                FROM service_catalog.service_types
                WHERE {where_clause};
                """,
                *params,
            )
            return [_mapper(row) for row in rows], int(total or 0)

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={
                "q": filters.q,
                "is_active": filters.is_active,
                "is_primary": filters.is_primary,
                "min_price": (
                    str(filters.min_price) if filters.min_price is not None else None
                ),
                "max_price": (
                    str(filters.max_price) if filters.max_price is not None else None
                ),
                "limit": limit,
                "offset": offset,
            },
            operation_name="list service types",
        )
