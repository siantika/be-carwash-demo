from dataclasses import dataclass

from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction
from app.modules.billing.domain.value_objects.payment import PaymentMethodEnum
from app.modules.billing.domain.value_objects.payment_state import PaymentStatus


@dataclass(frozen=True)
class TransactionListFilterDto:
    ticket_id: int | None = None
    cashier_id: int | None = None
    payment_method: PaymentMethodEnum | str | None = None
    payment_status: PaymentStatus | str | None = None
    plate_number: str | None = None


@dataclass(frozen=True)
class TransactionRecord:
    transaction: PaymentTransaction
    ticket_number: str
    cashier: str
