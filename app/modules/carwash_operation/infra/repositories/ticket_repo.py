from typing import Any, Mapping

import asyncpg

from app.modules.carwash_operation.domain.entities.ticket import (
    Ticket,
    TicketStatusEnum,
)
from app.modules.carwash_operation.domain.repositories.i_ticket_repo import (
    ITicketRepository,
)
from app.modules.carwash_operation.domain.value_objects.entry_time import EntryTime
from app.modules.carwash_operation.domain.value_objects.service_snapshot import (
    ServiceSnapshot,
)
from app.modules.carwash_operation.domain.value_objects.ticket_number import (
    TicketNumber,
)
from app.shared.domain.exceptions.exceptions import EntityAlreadyExists, RepositoryError
from app.shared.domain.value_objects.money import Money
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger

Row = asyncpg.Record | Mapping[str, Any]

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


def _mapper(row: Row) -> Ticket:
    if row is None:
        raise RepositoryError("Ticket row is None")

    return Ticket(
        id=row["id"],
        service_type_id=row["service_type_id"],
        service_snapshot=ServiceSnapshot(
            service_name=row["service_name_snapshot"],
            service_desc=row["service_desc_snapshot"],
            service_price=Money(row["service_base_price_snapshot"]),
        ),
        ticket_number=TicketNumber(row["ticket_number"]),
        entry_time=EntryTime(row["entry_time"]),
        status=TicketStatusEnum(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AsyncPgTicketRepository(ITicketRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def find_by_id(self, ticket_id: int) -> Ticket | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM carwash_operation.tickets
                WHERE id = $1;
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

    async def list(
        self,
        *,
        status: TicketStatusEnum | None,
        service_type_id: int | None,
        ticket_number: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Ticket], int]:
        async def _fetch():
            conditions: list[str] = []
            params: list[Any] = []

            if status is not None:
                params.append(status.value)
                conditions.append(f"status = ${len(params)}")

            if service_type_id is not None:
                params.append(service_type_id)
                conditions.append(f"service_type_id = ${len(params)}")

            if ticket_number is not None:
                params.append(f"%{ticket_number}%")
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
                "status": status.value if status is not None else None,
                "service_type_id": service_type_id,
                "ticket_number": ticket_number,
                "limit": limit,
                "offset": offset,
            },
            operation_name="list carwash_operation.tickets",
        )

    async def add(self, ticket: Ticket) -> Ticket:
        async def _create():
            try:
                row = await self.db.fetchrow(
                    f"""
                    INSERT INTO carwash_operation.tickets (
                        service_type_id,
                        service_name_snapshot,
                        service_desc_snapshot,
                        service_base_price_snapshot,
                        ticket_number,
                        entry_time,
                        status
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING {SELECT_ALL_COLUMNS};
                    """,
                    ticket.service_type_id,
                    ticket.service_snapshot.service_name,
                    ticket.service_snapshot.service_desc,
                    ticket.service_snapshot.service_price.amount,
                    ticket.ticket_number.value,
                    ticket.entry_time.value,
                    ticket.status.value,
                )
            except asyncpg.UniqueViolationError as exc:
                raise EntityAlreadyExists("Ticket", ticket.ticket_number.value) from exc

            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={
                "ticket_number": ticket.ticket_number.value,
                "service_type_id": ticket.service_type_id,
            },
            operation_name="create ticket",
        )

    async def save(self, ticket: Ticket) -> Ticket:
        async def _update():
            row = await self.db.fetchrow(
                f"""
                UPDATE carwash_operation.tickets
                SET service_type_id = $1,
                    service_name_snapshot = $2,
                    service_desc_snapshot = $3,
                    service_base_price_snapshot = $4,
                    ticket_number = $5,
                    entry_time = $6,
                    status = $7,
                    updated_at = NOW()
                WHERE id = $8
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                ticket.service_type_id,
                ticket.service_snapshot.service_name,
                ticket.service_snapshot.service_desc,
                ticket.service_snapshot.service_price.amount,
                ticket.ticket_number.value,
                ticket.entry_time.value,
                ticket.status.value,
                ticket.id,
            )
            if row is None:
                raise RepositoryError("Ticket not found")

            return _mapper(row)

        return await handle_db_error(
            operation=_update,
            logger=self.logger,
            context={"ticket_id": ticket.id},
            operation_name="update ticket",
        )
