from dataclasses import dataclass, field
from enum import Enum

from app.modules.carwash_operation.domain.value_objects.entry_time import EntryTime
from app.modules.carwash_operation.domain.value_objects.service_snapshot import (
    ServiceSnapshot,
)
from app.modules.carwash_operation.domain.value_objects.ticket_number import TicketNumber
from app.shared.domain.entities.base import BaseEntity
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    InvalidTargetTicketStateError,
    TerminalTicketStateError,
)


class TicketStatusEnum(str, Enum):
    VOID = "VOID"
    PAID = "PAID"
    IN_PROGRESS = "IN_PROGRESS"


@dataclass(kw_only=True)
class Ticket(BaseEntity):
    service_type_id: int
    service_snapshot: ServiceSnapshot
    ticket_number: TicketNumber
    entry_time: EntryTime = field(default_factory=EntryTime)
    status: TicketStatusEnum = TicketStatusEnum.IN_PROGRESS

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.service_type_id < 1:
            raise BusinessRuleViolation("Ticket.service_type_id must be >= 1")

        if isinstance(self.status, str):
            self.status = TicketStatusEnum(self.status)

    def change_status(self, new_status: TicketStatusEnum) -> None:
        if self.status in [TicketStatusEnum.PAID, TicketStatusEnum.VOID]:
            raise TerminalTicketStateError(
                f"Cannot change status from terminal state '{self.status}'."
            )

        if new_status not in TicketStatusEnum:
            raise InvalidTargetTicketStateError(f"Invalid target status '{new_status}'.")

        self.status = new_status

    def mark_paid(self) -> None:
        self.change_status(TicketStatusEnum.PAID)

    def mark_void(self) -> None:
        self.change_status(TicketStatusEnum.VOID)
