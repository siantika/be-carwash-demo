from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.identity.domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def list(self, limit:int, offset:int ) -> List[User]:
        pass 

    @abstractmethod
    async def add(self, user:User) -> User:
        pass
    
    @abstractmethod
    async def save(self, user:User) -> User:
        pass

