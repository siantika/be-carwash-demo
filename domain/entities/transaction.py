from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from domain.entities.base import BaseEntity
from domain.exceptions import BusinessRuleViolation
from domain.value_object.money import Money
from domain.value_object.payment import Payment
from domain.value_object.payment_state import PaymentState
from domain.value_object.plate_number import PlateNumber


class PaymentMethodEnum(str, Enum):
    CASH = "CASH"
    QRIS = "QRIS"
    TRANSFER = "TRANSFER"
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


@dataclass
class Transaction(BaseEntity):
    ticket_id: int
    user_id: int # should be checked in use case. The allowed role only "CASHIER"

    plate_number: PlateNumber

    payment: Payment
    payment_status:PaymentState

    subtotal_amount: Money = field(default_factory=lambda: Money("0"))
    total_amount: Money = field(default_factory=lambda: Money("0"))


    def __post_init__(self) -> None:
        if self.ticket_id < 1:
            raise BusinessRuleViolation("Transaction.ticket_id must be >= 1")
        if self.user_id < 1:
            raise BusinessRuleViolation("Transaction.cashier_id must be >= 1")
