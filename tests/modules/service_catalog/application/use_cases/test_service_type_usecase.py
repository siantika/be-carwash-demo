from decimal import Decimal

import pytest

from app.modules.service_catalog.application.dto.service_type_dto import (
    CreateServiceTypeCmd,
    UpdateServiceTypeCmd,
)
from app.modules.service_catalog.application.use_cases.service_type_usecase import (
    ActivateServiceTypeUseCase,
    ChangeServiceTypeDataUseCase,
    CreateServiceTypeUseCase,
    DeactivateServiceTypeUseCase,
    ListServiceTypesUseCase,
)
from app.modules.service_catalog.domain.entities.service_type import ServiceType
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityAlreadyExists,
)
from app.shared.domain.value_objects.money import Money


class FakeServiceTypeRepository:
    def __init__(self):
        self.service_types: dict[int, ServiceType] = {}
        self.next_id = 1

    async def get_by_id(self, service_type_id: int) -> ServiceType | None:
        return self.service_types.get(service_type_id)

    async def get_by_name(self, service_name: str) -> ServiceType | None:
        return next(
            (
                service_type
                for service_type in self.service_types.values()
                if service_type.name == service_name
            ),
            None,
        )

    async def list(self, limit: int, offset: int) -> tuple[list[ServiceType], int]:
        service_types = list(self.service_types.values())
        service_types.sort(key=lambda service_type: service_type.id or 0, reverse=True)
        return service_types[offset:offset + limit], len(service_types)

    async def add(self, service_type: ServiceType) -> ServiceType:
        service_type.id = self.next_id
        self.next_id += 1
        self.service_types[service_type.id] = service_type
        return service_type

    async def save(self, service_type: ServiceType) -> ServiceType:
        self.service_types[service_type.id] = service_type
        return service_type


@pytest.mark.anyio
async def test_create_service_type_saves_new_service() -> None:
    repo = FakeServiceTypeRepository()
    usecase = CreateServiceTypeUseCase(repo)

    result = await usecase.execute(
        CreateServiceTypeCmd(
            name="Premium Wash",
            desc="Premium exterior wash",
            price=Decimal("75000"),
            is_active=True,
            is_primary=False,
        )
    )

    assert result.id == 1
    assert result.name == "Premium Wash"
    assert result.price == Decimal("75000")
    assert repo.service_types[1].price == Money(Decimal("75000"))


@pytest.mark.anyio
async def test_create_service_type_rejects_duplicate_name() -> None:
    repo = FakeServiceTypeRepository()
    usecase = CreateServiceTypeUseCase(repo)
    cmd = CreateServiceTypeCmd(
        name="Premium Wash",
        desc="Premium exterior wash",
        price=Decimal("75000"),
    )

    await usecase.execute(cmd)

    with pytest.raises(EntityAlreadyExists):
        await usecase.execute(cmd)


@pytest.mark.anyio
async def test_list_service_types_paginates_results() -> None:
    repo = FakeServiceTypeRepository()
    for index in range(5):
        await repo.add(
            ServiceType(
                name=f"Service {index}",
                desc=f"Service desc {index}",
                price=Money(Decimal("10000")),
            )
        )

    result = await ListServiceTypesUseCase(repo).execute(page=2, limit=2)

    assert [service_type.name for service_type in result.items] == ["Service 2", "Service 1"]
    assert result.total == 5
    assert result.page == 2
    assert result.limit == 2


@pytest.mark.anyio
async def test_update_service_type_changes_partial_fields() -> None:
    repo = FakeServiceTypeRepository()
    service_type = await repo.add(
        ServiceType(
            name="Basic Wash",
            desc="Basic exterior wash",
            price=Money(Decimal("50000")),
        )
    )

    result = await ChangeServiceTypeDataUseCase(repo).execute(
        service_type.id,
        UpdateServiceTypeCmd(
            name="Basic Wash Plus",
            price=Decimal("55000"),
        ),
    )

    assert result.name == "Basic Wash Plus"
    assert result.desc == "Basic exterior wash"
    assert result.price == Decimal("55000")


@pytest.mark.anyio
async def test_deactivate_primary_service_is_rejected() -> None:
    repo = FakeServiceTypeRepository()
    service_type = await repo.add(
        ServiceType(
            name="Primary Wash",
            desc="Primary exterior wash",
            price=Money(Decimal("50000")),
            is_primary=True,
        )
    )

    with pytest.raises(BusinessRuleViolation):
        await DeactivateServiceTypeUseCase(repo).execute(service_type.id)


@pytest.mark.anyio
async def test_activate_service_type_sets_active() -> None:
    repo = FakeServiceTypeRepository()
    service_type = await repo.add(
        ServiceType(
            name="Basic Wash",
            desc="Basic exterior wash",
            price=Money(Decimal("50000")),
            is_active=False,
        )
    )

    result = await ActivateServiceTypeUseCase(repo).execute(service_type.id)

    assert result.is_active is True
