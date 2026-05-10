from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


class PaymentStatus(Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"

@dataclass(frozen=True)
class PaymentState:
    status: PaymentStatus
    paid_at: Optional[datetime] = None

    def __post_init__(self):
        if self.status == PaymentStatus.PAID:
            if self.paid_at is None:
                raise BusinessRuleViolation(
                    "paid_at must be set when payment status is PAID"
                )
            if self.paid_at.tzinfo is None:
                raise BusinessRuleViolation("paid_at must be timezone-aware")
        else:
            if self.paid_at is not None:
                raise BusinessRuleViolation(
                    f"paid_at must be None when payment status is {self.status}"
                )
