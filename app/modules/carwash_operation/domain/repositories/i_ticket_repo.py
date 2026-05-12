from typing import Protocol

from app.modules.carwash_operation.domain.entities.ticket import Ticket, TicketStatusEnum


class ITicketRepository(Protocol):
    async def find_by_id(self, ticket_id: int) -> Ticket | None: ...

    async def list(
        self,
        *,
        status: TicketStatusEnum | None,
        service_type_id: int | None,
        ticket_number: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Ticket], int]: ...

    async def add(self, ticket: Ticket) -> Ticket: ...

    async def save(self, ticket: Ticket) -> Ticket: ...
