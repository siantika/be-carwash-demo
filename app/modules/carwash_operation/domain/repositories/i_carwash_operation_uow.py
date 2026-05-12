from typing import Protocol

from app.modules.carwash_operation.domain.repositories.i_ticket_repo import ITicketRepository
from app.modules.carwash_operation.domain.repositories.i_ticket_void_repo import (
    ITicketVoidRepository,
)
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository


class ICarwashOperationUnitOfWork(Protocol):
    ticket: ITicketRepository
    ticket_void: ITicketVoidRepository
    account: IAccountRepository

    async def __aenter__(self) -> "ICarwashOperationUnitOfWork": ...

    async def __aexit__(self, exc_type, exc, tb): ...

    async def commit(self): ...

    async def rollback(self): ...
