from typing import Any

import asyncpg

from app.modules.carwash_operation.application.queries.models import (
    TicketListFilterDto,
)
from app.modules.carwash_operation.application.queries.ticket_query_repository import (
    ITicketQueryRepository,
)
from app.modules.carwash_operation.infra.repositories.ticket_repo import (
    SELECT_ALL_COLUMNS,
    _mapper,
)
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger


class PostgresTicketQueryRepository(ITicketQueryRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def list(
        self,
        *,
        filters: TicketListFilterDto,
        limit: int,
        offset: int,
    ):
        async def _fetch():
            conditions: list[str] = []
            params: list[Any] = []

            if filters.status is not None:
                params.append(filters.status.value)
                conditions.append(f"status = ${len(params)}")

            if filters.service_type_id is not None:
                params.append(filters.service_type_id)
                conditions.append(f"service_type_id = ${len(params)}")

            if filters.ticket_number is not None:
                params.append(f"%{filters.ticket_number}%")
                conditions.append(f"ticket_number ILIKE ${len(params)}")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            limit_param = len(params) + 1
            offset_param = len(params) + 2

            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM carwash_operation.tickets
                {where_clause}
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
                FROM carwash_operation.tickets
                {where_clause};
                """,
                *params,
            )
            return [_mapper(row) for row in rows], int(total or 0)

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={
                "status": filters.status.value if filters.status is not None else None,
                "service_type_id": filters.service_type_id,
                "ticket_number": filters.ticket_number,
                "limit": limit,
                "offset": offset,
            },
            operation_name="list carwash_operation.tickets",
        )
