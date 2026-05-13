from typing import Protocol

from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction


class ITransactionRepository(Protocol):
    async def find_by_id(self, transaction_id: int) -> PaymentTransaction | None: ...

    async def find_by_ticket_id(self, ticket_id: int) -> PaymentTransaction | None: ...

    async def add(self, transaction: PaymentTransaction) -> PaymentTransaction: ...
