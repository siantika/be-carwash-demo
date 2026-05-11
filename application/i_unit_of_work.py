from abc import ABC, abstractmethod

from domain.repositories.i_service_type import IServiceTypeRepository
from domain.repositories.i_ticket_repo import ITicketRepository
from domain.repositories.i_transaction_repo import ITransactionRepository
from domain.repositories.i_void_ticket_repo import ITicketVoidRepository


class IUnitOfWork(ABC):
    ticket: ITicketRepository
    ticket_void : ITicketVoidRepository
    transaction: ITransactionRepository
    service_type: IServiceTypeRepository
  
    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork":
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb):
        ...

    @abstractmethod
    async def commit(self):
        ...

    @abstractmethod
    async def rollback(self):
        ...
