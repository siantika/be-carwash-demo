from dataclasses import dataclass

from app.modules.carwash_operation.domain.entities.ticket import TicketStatusEnum


@dataclass(frozen=True)
class TicketListFilterDto:
    status: TicketStatusEnum | str | None = None
    service_type_id: int | None = None
    ticket_number: str | None = None
