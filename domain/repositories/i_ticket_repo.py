from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.ticket import Ticket


class ITicketRepository(ABC):
    @abstractmethod
    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        pass
    
    @abstractmethod
    async def list(self, limit:int, offset:int) -> List[Ticket]:
        pass

    @abstractmethod
    async def add(self, ticket: Ticket) -> Ticket:
        pass

    @abstractmethod
    async def save(self, ticket:Ticket) -> Ticket:
        pass

