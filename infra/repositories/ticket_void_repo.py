import asyncpg

from app.shared.infra.database.error_handler import handle_db_error
from domain.entities.ticket_void import TicketVoid
from domain.repositories.i_void_ticket_repo import ITicketVoidRepository
from interfaces.i_logger import ILogger


def _mapper(row: asyncpg.Record) -> TicketVoid:
    return TicketVoid(
        id = row['id'],
        ticket_id= row['ticket_id'],
        user_id= row['user_id'],
        reason= row['reason'],
        void_time= row['void_time']
    )

class AsyncPgTicketVoidRepository(ITicketVoidRepository):
    def __init__(self, db: asyncpg.Connection, logger:ILogger):
        self.db = db
        self.logger = logger

    async def add(self, data: TicketVoid) -> TicketVoid:
        async def _create():
            row = await self.db.fetchrow(
                """
                INSERT INTO ticket_voids (
                    ticket_id,
                    reason,
                    user_id,
                    void_time
                )
                VALUES ($1, $2, $3, $4)
                RETURNING
                    id,
                    ticket_id,
                    user_id,
                    reason,
                    void_time;
                """,
                data.ticket_id,
                data.reason,
                data.user_id,
                data.void_time,
            )
            return _mapper(row)
        return await handle_db_error(
            operation= _create,
            logger=self.logger,
            context={"ticket_id": TicketVoid.id},
            operation_name="create ticket void by id"
        )

