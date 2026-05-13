from app.modules.service_catalog.application.dto.service_type_dto import (
    ServiceTypeListResultDto,
    ServiceTypeResultDto,
)
from app.modules.service_catalog.application.dto.service_type_mapper import (
    to_service_type_result,
)
from app.modules.service_catalog.application.queries.models import (
    ServiceTypeListFilterDto,
)
from app.modules.service_catalog.domain.repositories.i_service_type_repo import (
    IServiceTypeRepository,
)
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation, EntityNotFound


class ListServiceTypesUseCase:
    def __init__(self, service_type_query):
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
            items=[to_service_type_result(service_type) for service_type in service_types],
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

        return to_service_type_result(service_type)


class FindServiceTypeByNameUseCase:
    def __init__(self, service_type_repo: IServiceTypeRepository):
        self.service_type_repo = service_type_repo

    async def execute(self, service_name: str) -> ServiceTypeResultDto:
        name = service_name.strip()
        service_type = await self.service_type_repo.find_by_name(name)
        if service_type is None:
            raise EntityNotFound("ServiceType", name)

        return to_service_type_result(service_type)
