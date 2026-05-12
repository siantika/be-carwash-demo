from typing import Protocol

from app.modules.carwash_operation.domain.entities.ticket_void import TicketVoid


class ITicketVoidRepository(Protocol):
    async def add(self, ticket_void: TicketVoid) -> TicketVoid: ...
