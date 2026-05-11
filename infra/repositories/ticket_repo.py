from typing import List, Optional

import asyncpg

from app.shared.infra.database.error_handler import handle_db_error
from domain.entities.ticket import Ticket, TicketStatusEnum
from domain.value_object.entry_time import EntryTime
from domain.value_object.money import Money
from domain.value_object.service_snapshot import ServiceSnapshot
from domain.value_object.ticket_number import TicketNumber
from interfaces.i_logger import ILogger

SELECT_ALL_COLUMNS = """
id,
service_type_id,
service_name_snapshot,
service_desc_snapshot,
service_base_price_snapshot,
ticket_number,
entry_time,
status,
created_at,
updated_at
""".strip()


def _mapper(row: asyncpg.Record) -> Ticket:
    service_snapshot = ServiceSnapshot(
        service_name= row["service_name_snapshot"],
        service_desc= row["service_desc_snapshot"],
        service_price= Money(row["service_base_price_snapshot"]),
    )
    return Ticket(
        id=row["id"],
        service_type_id=row["service_type_id"],
        service_snapshot= service_snapshot,
        ticket_number=TicketNumber(row["ticket_number"]),
        entry_time=EntryTime(row["entry_time"]),
        status=TicketStatusEnum(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncPgTicketRepository:
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM tickets
                WHERE id = $1
                """,
                ticket_id,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"ticket_id": ticket_id},
            operation_name="fetch ticket by id",
        )

    async def list(self, limit: int, offset:int) -> List[Ticket]:
        async def _fetch():
            rows = await self.db.fetch(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM tickets
                ORDER BY created_at DESC, id DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset
            )
            return [_mapper(row) for row in rows]
        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={},
            operation_name="list tickets",
        )


    async def add(self, data: Ticket) -> Ticket:
        async def _create():
            row = await self.db.fetchrow(
                f"""
                INSERT INTO tickets (
                    service_type_id,
                    service_name_snapshot,
                    service_desc_snapshot,
                    service_base_price_snapshot,
                    ticket_number,
                    entry_time,
                    status
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                RETURNING {SELECT_ALL_COLUMNS}
                """,
                data.service_type_id,
                data.service_snapshot.service_name,            
                data.service_snapshot.service_desc,            
                data.service_snapshot.service_price.amount, # Use Decimal here since this is outside the domain (Money VO boundary)
                data.ticket_number.value,                      
                data.entry_time.value,                         
                data.status.value,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={
                "ticket_id": None,
                "ticket_number": data.ticket_number.value,
                "service_type_id": data.service_type_id,
            },
            operation_name="create ticket",
        )

    async def save(self, data: Ticket) -> Ticket:
        async def _update():
            row = await self.db.fetchrow(
                f"""
                UPDATE tickets
                SET service_type_id = $1,
                    service_name_snapshot = $2,
                    service_desc_snapshot = $3,
                    service_base_price_snapshot = $4,
                    ticket_number = $5,
                    entry_time = $6,
                    status = $7,
                    updated_at = now()
                WHERE id = $8
                RETURNING {SELECT_ALL_COLUMNS}
                """,
                data.service_type_id,
                data.service_snapshot.service_name,
                data.service_snapshot.service_desc,
                data.service_snapshot.service_price.amount,
                data.ticket_number.value,
                data.entry_time.value,
                data.status.value,
                data.id,
            )
            return _mapper(row)

        return await handle_db_error(
            operation=_update,
            logger=self.logger,
            context={"ticket_id": data.id},
            operation_name="update ticket",
        )
