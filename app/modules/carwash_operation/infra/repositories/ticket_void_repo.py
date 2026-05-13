from typing import Any, Mapping

import asyncpg

from app.modules.carwash_operation.domain.entities.ticket_void import TicketVoid
from app.modules.carwash_operation.domain.repositories.i_ticket_void_repo import (
    ITicketVoidRepository,
)
from app.shared.domain.exceptions.exceptions import RepositoryError
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger

Row = asyncpg.Record | Mapping[str, Any]


def _mapper(row: Row) -> TicketVoid:
    if row is None:
        raise RepositoryError("Ticket void row is None")

    return TicketVoid(
        id=row["id"],
        ticket_id=row["ticket_id"],
        account_id=row["account_id"],
        reason=row["reason"],
        void_time=row["void_time"],
    )


class AsyncPgTicketVoidRepository(ITicketVoidRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def add(self, ticket_void: TicketVoid) -> TicketVoid:
        async def _create():
            row = await self.db.fetchrow(
                """
                INSERT INTO carwash_operation.ticket_voids (
                    ticket_id,
                    reason,
                    account_id,
                    void_time
                )
                VALUES ($1, $2, $3, $4)
                RETURNING
                    id,
                    ticket_id,
                    account_id,
                    reason,
                    void_time;
                """,
                ticket_void.ticket_id,
                ticket_void.reason,
                ticket_void.account_id,
                ticket_void.void_time,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={
                "ticket_id": ticket_void.ticket_id,
                "account_id": ticket_void.account_id,
            },
            operation_name="create ticket void",
        )
