from app.shared.domain.exceptions.exceptions import EntityNotFound
from application.dto.service_type_dto import ServiceTypeResultDto, UpdateServiceTypeCmd
from domain.repositories.i_service_type import IServiceTypeRepository


class ChangeServiceTypeDataUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(
        self,
        service_type_id: int,
        cmd: UpdateServiceTypeCmd,
    ) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.get_by_id(service_type_id)
        if not service_type:
            raise EntityNotFound(f"Service with id '{service_type_id}' is not found")

        service_type.update_details(
            name=cmd.name,
            desc=cmd.desc,
            price=cmd.price,
            is_active=cmd.is_active,
            is_primary=cmd.is_primary,
        )
        
        updated_service_type = await self.service_type_repo.save(service_type)
        return ServiceTypeResultDto(
            id  = updated_service_type.id,
            name = updated_service_type.name,
            desc= updated_service_type.desc,
            price= updated_service_type.price,
            is_active= updated_service_type.is_active,
            is_primary= updated_service_type.is_primary,
            created_at= updated_service_type.created_at,
            updated_at= updated_service_type.updated_at
        )

    