from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.modules.carwash_operation.domain.entities.ticket import TicketStatusEnum


@dataclass(frozen=True)
class CreateTicketCmd:
    service_type_id: int


@dataclass(frozen=True)
class TicketListFilterDto:
    status: TicketStatusEnum | str | None = None
    service_type_id: int | None = None
    ticket_number: str | None = None


@dataclass(frozen=True)
class TicketResultDto:
    id: int
    ticket_number: str
    entry_time: datetime
    status: str
    service_type_id: int
    service_name: str
    service_desc: str
    service_price: Decimal
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TicketListResultDto:
    items: list[TicketResultDto]
    total: int
    page: int
    limit: int
