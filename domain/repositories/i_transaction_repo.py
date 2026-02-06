from abc import ABC, abstractmethod
from typing import List, Optional

from application.dto.transaction_dto import TransactionResultDto
from domain.entities.transaction import Transaction


class ITransactionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, transaction_id:int) -> Optional[Transaction]:
        pass 
    
    @abstractmethod
    async def list(self, limit:int, offset:int) -> List[TransactionResultDto]:
        pass 
    
    @abstractmethod
    async def get_by_ticket_id(self, ticket_id:int) -> Optional[Transaction]:
        pass 
    
    @abstractmethod
    async def add(self, data:Transaction)-> Transaction:
        pass 
    