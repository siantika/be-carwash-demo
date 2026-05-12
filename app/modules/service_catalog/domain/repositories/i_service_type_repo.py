from decimal import Decimal
from typing import Protocol

from app.modules.service_catalog.domain.entities.service_type import ServiceType


class IServiceTypeRepository(Protocol):
    async def find_by_id(self, service_type_id: int) -> ServiceType | None: ...

    async def find_by_name(self, service_name: str) -> ServiceType | None: ...

    async def list(
        self,
        *,
        q: str | None,
        is_active: bool | None,
        is_primary: bool | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ServiceType], int]: ...

    async def add(self, service_type: ServiceType) -> ServiceType: ...

    async def save(self, service_type: ServiceType) -> ServiceType: ...

    async def delete(self, service_type: ServiceType) -> ServiceType: ...
