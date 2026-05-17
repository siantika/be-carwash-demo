from typing import Protocol

from app.modules.carwash_operation.domain.entities.ticket import Ticket


class ITicketRepository(Protocol):
    async def find_by_id(self, ticket_id: int) -> Ticket | None: ...

    async def add(self, ticket: Ticket) -> Ticket: ...

    async def save(self, ticket: Ticket) -> Ticket: ...
