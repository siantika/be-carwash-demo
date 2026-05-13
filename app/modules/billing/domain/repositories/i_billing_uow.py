from typing import Protocol

from app.modules.billing.domain.repositories.i_transaction_repo import (
    ITransactionRepository,
)
from app.modules.billing.domain.repositories.i_idempotency_repo import (
    IIdempotencyRepository,
)
from app.modules.carwash_operation.domain.repositories.i_ticket_repo import ITicketRepository
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository


class IBillingUnitOfWork(Protocol):
    transaction: ITransactionRepository
    idempotency: IIdempotencyRepository
    ticket: ITicketRepository
    account: IAccountRepository

    async def __aenter__(self) -> "IBillingUnitOfWork": ...

    async def __aexit__(self, exc_type, exc, tb): ...

    async def commit(self): ...

    async def rollback(self): ...
