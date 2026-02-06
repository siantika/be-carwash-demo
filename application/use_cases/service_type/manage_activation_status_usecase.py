from application.dto.service_type_dto import (
    ServiceTypeResultDto,
)
from domain.exceptions import EntityNotFound
from domain.repositories.i_service_type import IServiceTypeRepository


class ActivateStatusServiceTypeUseCase:
    def __init__(self, service_type_repo:IServiceTypeRepository):
        self.service_type_repo = service_type_repo
        
    async def execute(self, service_type_id:int)-> ServiceTypeResultDto:
        service_type = await self.service_type_repo.get_by_id(service_type_id)
        if not service_type:
            raise EntityNotFound(f"Service type with id: {service_type_id} not found!")
        
        service_type.activate()
        activated_service_type =  await self.service_type_repo.save(service_type)
        return ServiceTypeResultDto(
            id  = activated_service_type.id,
            name = activated_service_type.name,
            desc= activated_service_type.desc,
            price= activated_service_type.price.amount,
            is_active= activated_service_type.is_active,
            is_primary= activated_service_type.is_primary,
            created_at= activated_service_type.created_at,
            updated_at= activated_service_type.updated_at
        )


class DeactivateStatusServiceTypeUseCase:
    def __init__(self, service_type_repo:IServiceTypeRepository):
        self.service_type_repo = service_type_repo
        
    async def execute(self, service_type_id:int)-> ServiceTypeResultDto:
        service_type = await self.service_type_repo.get_by_id(service_type_id)
        if not service_type:
            raise EntityNotFound(f"Service type with id: {service_type_id} not found!")
        
        service_type.deactivate()
        
        deactivate_service_type = await self.service_type_repo.save(service_type)
        return ServiceTypeResultDto(
            id  = deactivate_service_type.id,
            name = deactivate_service_type.name,
            desc = deactivate_service_type.desc,
            price = deactivate_service_type.price.amount,
            is_active = deactivate_service_type.is_active,
            is_primary = deactivate_service_type.is_primary,
            created_at = deactivate_service_type.created_at,
            updated_at = deactivate_service_type.updated_at
        )