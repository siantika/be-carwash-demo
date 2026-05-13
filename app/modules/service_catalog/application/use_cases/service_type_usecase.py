from app.modules.service_catalog.application.dto.service_type_dto import (
    CreateServiceTypeCmd,
    ServiceTypeListResultDto,
    ServiceTypeResultDto,
    UpdateServiceTypeCmd,
)
from app.modules.service_catalog.application.queries.models import (
    ServiceTypeListFilterDto,
)
from app.modules.service_catalog.application.queries.service_type_query_repository import (
    IServiceTypeQueryRepository,
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
        return _to_service_type_result(created_service_type)


class ListServiceTypesUseCase:
    def __init__(self, service_type_query: IServiceTypeQueryRepository):
        self.service_type_query = service_type_query

    async def execute(
        self,
        filters: ServiceTypeListFilterDto | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> ServiceTypeListResultDto:
        if page < 1:
            raise BusinessRuleViolation("Page must be greater than or equal to 1")

        if limit < 1:
            raise BusinessRuleViolation("Limit must be greater than or equal to 1")

        filters = filters or ServiceTypeListFilterDto()
        q = filters.q.strip() if filters.q is not None else None
        if q == "":
            q = None

        if filters.min_price is not None and filters.min_price < 0:
            raise BusinessRuleViolation("Minimum price must be greater than or equal to 0")

        if filters.max_price is not None and filters.max_price < 0:
            raise BusinessRuleViolation("Maximum price must be greater than or equal to 0")

        if (
            filters.min_price is not None
            and filters.max_price is not None
            and filters.max_price < filters.min_price
        ):
            raise BusinessRuleViolation(
                "Maximum price must be greater than or equal to minimum price"
            )

        offset = (page - 1) * limit
        service_types, total = await self.service_type_query.list(
            filters=ServiceTypeListFilterDto(
                q=q,
                is_active=filters.is_active,
                is_primary=filters.is_primary,
                min_price=filters.min_price,
                max_price=filters.max_price,
            ),
            limit=limit,
            offset=offset,
        )
        return ServiceTypeListResultDto(
            items=[_to_service_type_result(service_type) for service_type in service_types],
            total=total,
            page=page,
            limit=limit,
        )


class FindServiceTypeByIdUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.find_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        return _to_service_type_result(service_type)


class FindServiceTypeByNameUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_name: str) -> ServiceTypeResultDto:
        name = service_name.strip()
        service_type = await self.service_type_repo.find_by_name(name)
        if service_type is None:
            raise EntityNotFound("ServiceType", name)

        return _to_service_type_result(service_type)


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
        return _to_service_type_result(updated_service_type)


class ActivateServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.find_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.activate()
        activated_service_type = await self.service_type_repo.save(service_type)
        return _to_service_type_result(activated_service_type)


class DeactivateServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> ServiceTypeResultDto:
        service_type = await self.service_type_repo.find_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.deactivate()
        deactivated_service_type = await self.service_type_repo.save(service_type)
        return _to_service_type_result(deactivated_service_type)


class DeleteServiceTypeUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_type_id: int) -> None:
        service_type = await self.service_type_repo.find_by_id(service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", service_type_id)

        service_type.delete(_utcnow())
        await self.service_type_repo.delete(service_type)
