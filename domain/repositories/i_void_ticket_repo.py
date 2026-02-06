from abc import ABC, abstractmethod

from domain.entities.ticket_void import TicketVoid


class ITicketVoidRepository(ABC):
    @abstractmethod
    async def add(self, ticket:TicketVoid) -> TicketVoid:
        pass 
    
