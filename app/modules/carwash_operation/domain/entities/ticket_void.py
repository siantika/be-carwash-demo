from dataclasses import dataclass, field
from datetime import datetime

from app.shared.domain.entities.base import BaseEntity, _utcnow
from app.shared.domain.exceptions.exceptions import InvalidValueObject


@dataclass(kw_only=True)
class TicketVoid(BaseEntity):
    ticket_id: int
    account_id: int
    reason: str
    void_time: datetime = field(default_factory=_utcnow)
    id: int | None = None

    def __post_init__(self):
        if self.ticket_id < 1:
            raise InvalidValueObject("Ticket id must be greater than or equal to 1")

        if self.account_id < 1:
            raise InvalidValueObject("Account id must be greater than or equal to 1")

        if not self.reason.strip():
            raise InvalidValueObject("Reason cannot be empty")

        self.reason = self.reason.strip()
