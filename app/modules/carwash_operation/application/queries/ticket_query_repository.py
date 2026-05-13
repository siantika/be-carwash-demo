from typing import Protocol

from app.modules.carwash_operation.application.queries.models import TicketListFilterDto
from app.modules.carwash_operation.domain.entities.ticket import Ticket


class ITicketQueryRepository(Protocol):
    async def list(
        self,
        *,
        filters: TicketListFilterDto,
        limit: int,
        offset: int,
    ) -> tuple[list[Ticket], int]: ...
