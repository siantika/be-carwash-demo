from dataclasses import dataclass
from enum import Enum

from app.shared.domain.entities.base import BaseEntity, _utcnow

from app.shared.domain.exceptions.exceptions import BusinessRuleViolation
from domain.value_object.entry_time import EntryTime
from domain.value_object.service_snapshot import ServiceSnapshot
from domain.value_object.ticket_number import TicketNumber


class TicketStatusEnum(str, Enum):
    VOID = "VOID"
    PAID = "PAID"
    IN_PROGRESS = "IN_PROGRESS"


@dataclass
class Ticket(BaseEntity):
    """
    Domain entity representing a carwash ticket.

    Business rules:
    - A new ticket is always created with status IN_PROGRESS.
    - Once marked as PAID or VOID, it cannot be changed again.
    """
    service_type_id: int
    service_snapshot: ServiceSnapshot
    ticket_number: TicketNumber
    entry_time: EntryTime = EntryTime(_utcnow())
    status: TicketStatusEnum = TicketStatusEnum.IN_PROGRESS

    def change_status(self, new_status: TicketStatusEnum) -> None :
        """
        Change status based on domain rules.

        Allowed transitions:
        - IN_PROGRESS → PAID
        - IN_PROGRESS → VOID
        - PAID and VOID → cannot be modified (terminal state)
        """
        if self.status in [TicketStatusEnum.PAID, TicketStatusEnum.VOID]:
            raise BusinessRuleViolation(f"Cannot change status from terminal state '{self.status}'.")
        
        if new_status not in TicketStatusEnum:
            raise BusinessRuleViolation(f"Invalid target status '{new_status}'.")

        self.status = new_status

    def mark_paid(self) -> None :
        self.change_status(TicketStatusEnum.PAID)
      
    def mark_void(self)-> None :
        self.change_status(TicketStatusEnum.VOID)
