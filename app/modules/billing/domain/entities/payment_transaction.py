from dataclasses import dataclass, field

from app.modules.billing.domain.value_objects.payment import Payment
from app.modules.billing.domain.value_objects.payment_state import PaymentState
from app.modules.billing.domain.value_objects.plate_number import PlateNumber
from app.shared.domain.entities.base import BaseEntity
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation
from app.shared.domain.value_objects.money import Money


@dataclass(kw_only=True)
class PaymentTransaction(BaseEntity):
    ticket_id: int
    cashier_id: int
    plate_number: PlateNumber
    payment: Payment
    payment_status: PaymentState
    subtotal_amount: Money = field(default_factory=lambda: Money("0"))
    total_amount: Money = field(default_factory=lambda: Money("0"))

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.ticket_id < 1:
            raise BusinessRuleViolation("PaymentTransaction.ticket_id must be >= 1")

        if self.cashier_id < 1:
            raise BusinessRuleViolation("PaymentTransaction.cashier_id must be >= 1")
