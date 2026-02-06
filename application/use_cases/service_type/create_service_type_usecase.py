from application.dto.service_type_dto import CreateServiceTypeCmd, ServiceTypeResultDto
from domain.entities.service_type import ServiceType
from domain.exceptions import EntityAlreadyExists
from domain.repositories.i_service_type import IServiceTypeRepository


class CreateServiceTypeUseCase:
    def __init__(self, service_type_repo:IServiceTypeRepository):
        self.service_type_repo = service_type_repo
        
    async def execute(self, cmd:CreateServiceTypeCmd)-> ServiceTypeResultDto:
        service_type = await self.service_type_repo.get_by_name(cmd.name)
        if service_type:
            raise EntityAlreadyExists(f"Service type with name: {cmd.name} already exist!")
        
        new_service_type = ServiceType(
            name=cmd.name,
            desc=cmd.desc,
            price=cmd.price,
            # Newly created entity is active by default
            is_active= cmd.is_active if cmd.is_active is not None else True,
            # Newly created entity is secondary by default
            is_primary= cmd.is_primary if cmd.is_primary is not None else False 
            
        )
        created_service_type = await self.service_type_repo.add(new_service_type)
        return ServiceTypeResultDto(
            id  = created_service_type.id,
            name = created_service_type.name,
            desc= created_service_type.desc,
            price= created_service_type.price.amount,
            is_active= created_service_type.is_active,
            is_primary= created_service_type.is_primary,
            created_at= created_service_type.created_at,
            updated_at= created_service_type.updated_at
        )

