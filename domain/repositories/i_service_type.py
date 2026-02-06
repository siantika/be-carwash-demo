from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.service_type import ServiceType


class IServiceTypeRepository(ABC):

    @abstractmethod
    async def get_by_id(self, service_type_id: int) -> Optional[ServiceType]:
        pass
    
    @abstractmethod
    async def get_by_name(self, service_name:str) -> List[ServiceType]:
        pass 
    
    @abstractmethod
    async def list(self, limit:int, offset:int) -> List[ServiceType]:
        pass 

    @abstractmethod
    async def add(self, service_type: ServiceType) -> ServiceType:
        pass

    @abstractmethod
    async def save(self, service_type: ServiceType) -> ServiceType:
        pass
