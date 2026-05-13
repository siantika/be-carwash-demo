from app.modules.service_catalog.application.dto.service_type_dto import (
    CreateServiceTypeCmd,
    ServiceTypeResultDto,
    UpdateServiceTypeCmd,
)
from app.modules.service_catalog.application.dto.service_type_mapper import (
    to_service_type_result,
)
from app.modules.service_catalog.domain.entities.service_type import ServiceType
from app.modules.service_catalog.domain.repositories.i_service_type_repo import (
    IServiceTypeRepository,
)
from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityAlreadyExists,
    EntityNotFound,
)
from app.shared.domain.value_objects.money import Money


class CreateServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, cmd: CreateServiceTypeCmd) -> ServiceTypeResultDto:
        name = cmd.name.strip()
        existing_service_type = await self.service_type_repo.find_by_name(name)
        if existing_service_type is not None:
            raise EntityAlreadyExists("ServiceType", name)

        service_type = ServiceType(
            name=name,
            desc=cmd.desc,
            price=Money(cmd.price),
            is_active=cmd.is_active,
            is_primary=cmd.is_primary,
        )
        created_service_type = await self.service_type_repo.add(service_type)
        return to_service_type_result(created_service_type)


class ChangeServiceTypeDataUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(
        self,
        service_type_id: int,
        cmd: UpdateServiceTypeCmd,
    ) -> ServiceTypeResultDto:
        if all(
            value is None
            for value in (
                cmd.name,
                cmd.desc,
                cmd.price,
                cmd.is_active,
                cmd.is_primary,
            )
        ):
            raise BusinessRuleViolation("At least one service type field must be provided")

        service_type = await self.service_type_repo.find_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        if cmd.name is not None:
            name = cmd.name.strip()
            existing_service_type = await self.service_type_repo.find_by_name(name)
            if (
                existing_service_type is not None
                and existing_service_type.id != service_type.id
            ):
                raise EntityAlreadyExists("ServiceType", name)

        service_type.update_details(
            name=cmd.name,
            desc=cmd.desc,
            price=Money(cmd.price) if cmd.price is not None else None,
            is_active=cmd.is_active,
            is_primary=cmd.is_primary,
        )
        updated_service_type = await self.service_type_repo.save(service_type)
        return to_service_type_result(updated_service_type)


class ActivateServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.find_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.activate()
        activated_service_type = await self.service_type_repo.save(service_type)
        return to_service_type_result(activated_service_type)


class DeactivateServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.find_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.deactivate()
        deactivated_service_type = await self.service_type_repo.save(service_type)
        return to_service_type_result(deactivated_service_type)


class DeleteServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> None:
        service_type = await self.service_type_repo.find_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.delete(_utcnow())
        await self.service_type_repo.delete(service_type)
