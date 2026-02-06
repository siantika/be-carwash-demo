from typing import List

from application.dto.service_type_dto import ServiceTypeResultDto
from domain.repositories.i_service_type import IServiceTypeRepository


class ListServiceTypesUseCase:
    def __init__(self, service_type_repo:IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, limit:int, offset:int )-> List[ServiceTypeResultDto]: 
        
        list_service_types = await self.service_type_repo.list(limit, offset)
        
        return [
            ServiceTypeResultDto(
                id = service_type.id,
                name= service_type.name,
                desc= service_type.desc,
                price = service_type.price.amount,
                is_active = service_type.is_active,
                is_primary = service_type.is_primary,
                created_at= service_type.created_at,
                updated_at= service_type.updated_at
            ) 
            for service_type in list_service_types
        ]
            

        
     