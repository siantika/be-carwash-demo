from typing import Protocol

from app.modules.service_catalog.application.queries.models import (
    ServiceTypeListFilterDto,
)
from app.modules.service_catalog.domain.entities.service_type import ServiceType


class IServiceTypeQueryRepository(Protocol):
    async def list(
        self,
        *,
        filters: ServiceTypeListFilterDto,
        limit: int,
        offset: int,
    ) -> tuple[list[ServiceType], int]: ...
