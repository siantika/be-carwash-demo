from decimal import Decimal

import pytest

from app.modules.service_catalog.application.dto.service_type_dto import (
    CreateServiceTypeCmd,
    UpdateServiceTypeCmd,
)
from app.modules.service_catalog.application.queries.models import (
    ServiceTypeListFilterDto,
)
from app.modules.service_catalog.application.queries.service_type_query import (
    FindServiceTypeByIdUseCase,
    FindServiceTypeByNameUseCase,
    ListServiceTypesUseCase,
)
from app.modules.service_catalog.application.commands.service_type_command import (
    ActivateServiceTypeUseCase,
    ChangeServiceTypeDataUseCase,
    CreateServiceTypeUseCase,
    DeleteServiceTypeUseCase,
    DeactivateServiceTypeUseCase,
)
from app.modules.service_catalog.domain.entities.service_type import ServiceType
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityAlreadyExists,
    EntityNotFound,
    PrimaryServiceCannotBeDeactivated,
    PrimaryServiceCannotBeDeleted,
)
from app.shared.domain.value_objects.money import Money


class FakeServiceTypeRepository:
    def __init__(self):
        self.service_types: dict[int, ServiceType] = {}
        self.next_id = 1

    async def find_by_id(self, service_type_id: int) -> ServiceType | None:
        return self.service_types.get(service_type_id)

    async def find_by_name(self, service_name: str) -> ServiceType | None:
        return next(
            (
                service_type
                for service_type in self.service_types.values()
                if service_type.name == service_name
            ),
            None,
        )

    async def list(
        self,
        *,
        filters: ServiceTypeListFilterDto,
        limit: int,
        offset: int,
    ) -> tuple[list[ServiceType], int]:
        service_types = list(self.service_types.values())

        if filters.q is not None:
            q_lower = filters.q.lower()
            service_types = [
                service_type
                for service_type in service_types
                if q_lower in service_type.name.lower()
                or q_lower in service_type.desc.lower()
            ]

        if filters.is_active is not None:
            service_types = [
                service_type
                for service_type in service_types
                if service_type.is_active is filters.is_active
            ]

        if filters.is_primary is not None:
            service_types = [
                service_type
                for service_type in service_types
                if service_type.is_primary is filters.is_primary
            ]

        if filters.min_price is not None:
            service_types = [
                service_type
                for service_type in service_types
                if service_type.price.amount >= filters.min_price
            ]

        if filters.max_price is not None:
            service_types = [
                service_type
                for service_type in service_types
                if service_type.price.amount <= filters.max_price
            ]

        service_types.sort(key=lambda service_type: service_type.id or 0, reverse=True)
        return service_types[offset : offset + limit], len(service_types)

    async def add(self, service_type: ServiceType) -> ServiceType:
        service_type.id = self.next_id
        self.next_id += 1
        self.service_types[service_type.id] = service_type
        return service_type

    async def save(self, service_type: ServiceType) -> ServiceType:
        self.service_types[service_type.id] = service_type
        return service_type

    async def delete(self, service_type: ServiceType) -> ServiceType:
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

    assert [service_type.name for service_type in result.items] == [
        "Service 2",
        "Service 1",
    ]
    assert result.total == 5
    assert result.page == 2
    assert result.limit == 2


@pytest.mark.anyio
async def test_list_service_types_applies_filters() -> None:
    repo = FakeServiceTypeRepository()
    await repo.add(
        ServiceType(
            name="Premium Wash",
            desc="Premium exterior wash",
            price=Money(Decimal("75000")),
        )
    )
    await repo.add(
        ServiceType(
            name="Basic Wash",
            desc="Basic exterior wash",
            price=Money(Decimal("50000")),
        )
    )
    await repo.add(
        ServiceType(
            name="Interior Cleaning",
            desc="Inactive interior cleaning",
            price=Money(Decimal("90000")),
            is_active=False,
        )
    )

    result = await ListServiceTypesUseCase(repo).execute(
        filters=ServiceTypeListFilterDto(
            q="wash",
            is_active=True,
            is_primary=False,
            min_price=Decimal("60000"),
            max_price=Decimal("80000"),
        )
    )

    assert [service_type.name for service_type in result.items] == ["Premium Wash"]
    assert result.total == 1


@pytest.mark.anyio
async def test_list_service_types_rejects_invalid_price_range() -> None:
    repo = FakeServiceTypeRepository()

    with pytest.raises(BusinessRuleViolation, match="Maximum price"):
        await ListServiceTypesUseCase(repo).execute(
            filters=ServiceTypeListFilterDto(
                min_price=Decimal("80000"),
                max_price=Decimal("50000"),
            )
        )


@pytest.mark.anyio
async def test_find_service_type_by_id_returns_service() -> None:
    repo = FakeServiceTypeRepository()
    service_type = await repo.add(
        ServiceType(
            name="Basic Wash",
            desc="Basic exterior wash",
            price=Money(Decimal("50000")),
        )
    )

    result = await FindServiceTypeByIdUseCase(repo).execute(service_type.id)

    assert result.id == service_type.id
    assert result.name == "Basic Wash"
    assert result.desc == "Basic exterior wash"
    assert result.price == Decimal("50000")


@pytest.mark.anyio
async def test_find_service_type_by_id_raises_when_missing() -> None:
    repo = FakeServiceTypeRepository()

    with pytest.raises(EntityNotFound):
        await FindServiceTypeByIdUseCase(repo).execute(999)


@pytest.mark.anyio
async def test_find_service_type_by_name_returns_service() -> None:
    repo = FakeServiceTypeRepository()
    service_type = await repo.add(
        ServiceType(
            name="Basic Wash",
            desc="Basic exterior wash",
            price=Money(Decimal("50000")),
        )
    )

    result = await FindServiceTypeByNameUseCase(repo).execute(" Basic Wash ")

    assert result.id == service_type.id
    assert result.name == "Basic Wash"
    assert result.price == Decimal("50000")


@pytest.mark.anyio
async def test_find_service_type_by_name_raises_when_missing() -> None:
    repo = FakeServiceTypeRepository()

    with pytest.raises(EntityNotFound):
        await FindServiceTypeByNameUseCase(repo).execute("Missing Wash")


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
async def test_update_service_type_rejects_empty_payload() -> None:
    repo = FakeServiceTypeRepository()

    with pytest.raises(BusinessRuleViolation, match="At least one"):
        await ChangeServiceTypeDataUseCase(repo).execute(
            1,
            UpdateServiceTypeCmd(),
        )


@pytest.mark.anyio
async def test_update_service_type_rejects_duplicate_name() -> None:
    repo = FakeServiceTypeRepository()
    await repo.add(
        ServiceType(
            name="Basic Wash",
            desc="Basic exterior wash",
            price=Money(Decimal("50000")),
        )
    )
    premium = await repo.add(
        ServiceType(
            name="Premium Wash",
            desc="Premium exterior wash",
            price=Money(Decimal("75000")),
        )
    )

    with pytest.raises(EntityAlreadyExists):
        await ChangeServiceTypeDataUseCase(repo).execute(
            premium.id,
            UpdateServiceTypeCmd(name="Basic Wash"),
        )


@pytest.mark.anyio
async def test_primary_service_is_forced_active() -> None:
    service_type = ServiceType(
        name="Primary Wash",
        desc="Primary exterior wash",
        price=Money(Decimal("50000")),
        is_active=False,
        is_primary=True,
    )

    assert service_type.is_active is True


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

    with pytest.raises(PrimaryServiceCannotBeDeactivated):
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


@pytest.mark.anyio
async def test_delete_service_type_soft_deletes_service() -> None:
    repo = FakeServiceTypeRepository()
    service_type = await repo.add(
        ServiceType(
            name="Basic Wash",
            desc="Basic exterior wash",
            price=Money(Decimal("50000")),
        )
    )

    await DeleteServiceTypeUseCase(repo).execute(service_type.id)

    assert repo.service_types[service_type.id].deleted_at is not None
    assert repo.service_types[service_type.id].is_active is False


@pytest.mark.anyio
async def test_delete_primary_service_is_rejected() -> None:
    repo = FakeServiceTypeRepository()
    service_type = await repo.add(
        ServiceType(
            name="Primary Wash",
            desc="Primary exterior wash",
            price=Money(Decimal("50000")),
            is_primary=True,
        )
    )

    with pytest.raises(
        PrimaryServiceCannotBeDeleted, match="Primary service cannot be deleted"
    ):
        await DeleteServiceTypeUseCase(repo).execute(service_type.id)

    assert repo.service_types[service_type.id].deleted_at is None
