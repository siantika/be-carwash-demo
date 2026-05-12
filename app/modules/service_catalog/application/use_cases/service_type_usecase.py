from app.modules.service_catalog.application.dto.service_type_dto import (
    CreateServiceTypeCmd,
    ServiceTypeListResultDto,
    ServiceTypeResultDto,
    UpdateServiceTypeCmd,
)
from app.modules.service_catalog.domain.entities.service_type import ServiceType
from app.modules.service_catalog.domain.repositories.i_service_type_repo import (
    IServiceTypeRepository,
)
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityAlreadyExists,
    EntityNotFound,
)
from app.shared.domain.value_objects.money import Money


def _to_service_type_result(service_type: ServiceType) -> ServiceTypeResultDto:
    return ServiceTypeResultDto(
        id=service_type.id,
        name=service_type.name,
        desc=service_type.desc,
        price=service_type.price.amount,
        is_active=service_type.is_active,
        is_primary=service_type.is_primary,
        created_at=service_type.created_at,
        updated_at=service_type.updated_at,
    )


class CreateServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, cmd: CreateServiceTypeCmd) -> ServiceTypeResultDto:
        existing_service_type = await self.service_type_repo.get_by_name(cmd.name)
        if existing_service_type is not None:
            raise EntityAlreadyExists("ServiceType", cmd.name)

        service_type = ServiceType(
            name=cmd.name,
            desc=cmd.desc,
            price=Money(cmd.price),
            is_active=cmd.is_active,
            is_primary=cmd.is_primary,
        )
        created_service_type = await self.service_type_repo.add(service_type)
        return _to_service_type_result(created_service_type)


class ListServiceTypesUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> ServiceTypeListResultDto:
        if page < 1:
            raise BusinessRuleViolation("Page must be greater than or equal to 1")

        if limit < 1:
            raise BusinessRuleViolation("Limit must be greater than or equal to 1")

        offset = (page - 1) * limit
        service_types, total = await self.service_type_repo.list(
            limit=limit,
            offset=offset,
        )
        return ServiceTypeListResultDto(
            items=[_to_service_type_result(service_type) for service_type in service_types],
            total=total,
            page=page,
            limit=limit,
        )


class ChangeServiceTypeDataUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(
        self,
        service_type_id: int,
        cmd: UpdateServiceTypeCmd,
    ) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.get_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.update_details(
            name=cmd.name,
            desc=cmd.desc,
            price=Money(cmd.price) if cmd.price is not None else None,
            is_active=cmd.is_active,
            is_primary=cmd.is_primary,
        )
        updated_service_type = await self.service_type_repo.save(service_type)
        return _to_service_type_result(updated_service_type)


class ActivateServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.get_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.activate()
        activated_service_type = await self.service_type_repo.save(service_type)
        return _to_service_type_result(activated_service_type)


class DeactivateServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.get_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.deactivate()
        deactivated_service_type = await self.service_type_repo.save(service_type)
        return _to_service_type_result(deactivated_service_type)
