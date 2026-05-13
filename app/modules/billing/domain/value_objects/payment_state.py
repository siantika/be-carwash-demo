from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


@dataclass(frozen=True)
class PaymentState:
    status: PaymentStatus
    paid_at: datetime | None = None

    def __post_init__(self):
        if isinstance(self.status, str):
            object.__setattr__(self, "status", PaymentStatus(self.status.strip().upper()))

        if self.status == PaymentStatus.PAID:
            if self.paid_at is None:
                raise BusinessRuleViolation("paid_at must be set when payment status is PAID")

            if self.paid_at.tzinfo is None or self.paid_at.tzinfo.utcoffset(self.paid_at) is None:
                raise BusinessRuleViolation("paid_at must be timezone-aware")
        elif self.paid_at is not None:
            raise BusinessRuleViolation(
                f"paid_at must be None when payment status is {self.status.value}"
            )
