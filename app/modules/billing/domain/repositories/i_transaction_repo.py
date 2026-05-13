from dataclasses import dataclass
from typing import Protocol

from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction
from app.modules.billing.domain.value_objects.payment import PaymentMethodEnum
from app.modules.billing.domain.value_objects.payment_state import PaymentStatus


@dataclass(frozen=True)
class TransactionRecord:
    transaction: PaymentTransaction
    ticket_number: str
    cashier: str


class ITransactionRepository(Protocol):
    async def find_by_id(self, transaction_id: int) -> PaymentTransaction | None: ...

    async def find_by_ticket_id(self, ticket_id: int) -> PaymentTransaction | None: ...

    async def list(
        self,
        *,
        ticket_id: int | None,
        cashier_id: int | None,
        payment_method: PaymentMethodEnum | None,
        payment_status: PaymentStatus | None,
        plate_number: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[TransactionRecord], int]: ...

    async def add(self, transaction: PaymentTransaction) -> PaymentTransaction: ...
