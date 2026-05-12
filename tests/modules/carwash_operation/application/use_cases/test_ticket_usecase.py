from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.modules.carwash_operation.application.dto.ticket_dto import (
    CreateTicketCmd,
    TicketListFilterDto,
)
from app.modules.carwash_operation.application.dto.ticket_void_dto import (
    CreateTicketVoidCmd,
)
from app.modules.carwash_operation.application.use_cases.ticket_usecase import (
    CreateTicketUseCase,
    ListTicketsUseCase,
    VoidTicketUseCase,
)
from app.modules.carwash_operation.domain.entities.ticket import Ticket, TicketStatusEnum
from app.modules.carwash_operation.domain.entities.ticket_void import TicketVoid
from app.modules.service_catalog.domain.entities.service_type import ServiceType
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation
from app.shared.domain.value_objects.money import Money


class FixedBarcodeGenerator:
    def generate(self) -> str:
        return "4006381333931"


class FakeServiceTypeRepository:
    def __init__(self):
        self.service_types: dict[int, ServiceType] = {}

    async def find_by_id(self, service_type_id: int) -> ServiceType | None:
        return self.service_types.get(service_type_id)


class FakeTicketRepository:
    def __init__(self):
        self.tickets: dict[int, Ticket] = {}
        self.next_id = 1

    async def find_by_id(self, ticket_id: int) -> Ticket | None:
        return self.tickets.get(ticket_id)

    async def list(
        self,
        *,
        status: TicketStatusEnum | None,
        service_type_id: int | None,
        ticket_number: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Ticket], int]:
        tickets = list(self.tickets.values())

        if status is not None:
            tickets = [ticket for ticket in tickets if ticket.status == status]

        if service_type_id is not None:
            tickets = [
                ticket for ticket in tickets if ticket.service_type_id == service_type_id
            ]

        if ticket_number is not None:
            tickets = [
                ticket
                for ticket in tickets
                if ticket_number in ticket.ticket_number.value
            ]

        tickets.sort(key=lambda ticket: ticket.id or 0, reverse=True)
        return tickets[offset:offset + limit], len(tickets)

    async def add(self, ticket: Ticket) -> Ticket:
        ticket.id = self.next_id
        self.next_id += 1
        self.tickets[ticket.id] = ticket
        return ticket

    async def save(self, ticket: Ticket) -> Ticket:
        self.tickets[ticket.id] = ticket
        return ticket


class FakeTicketVoidRepository:
    def __init__(self):
        self.ticket_voids: dict[int, TicketVoid] = {}
        self.next_id = 1

    async def add(self, ticket_void: TicketVoid) -> TicketVoid:
        ticket_void.id = self.next_id
        self.next_id += 1
        self.ticket_voids[ticket_void.id] = ticket_void
        return ticket_void


@dataclass
class FakeAccount:
    id: int


class FakeAccountRepository:
    def __init__(self):
        self.accounts: dict[int, FakeAccount] = {}

    async def find_by_id(self, account_id: int) -> FakeAccount | None:
        return self.accounts.get(account_id)


class FakeCarwashOperationUnitOfWork:
    def __init__(
        self,
        ticket_repo: FakeTicketRepository,
        ticket_void_repo: FakeTicketVoidRepository,
        account_repo: FakeAccountRepository,
    ):
        self.ticket = ticket_repo
        self.ticket_void = ticket_void_repo
        self.account = account_repo
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.committed = False


@pytest.mark.anyio
async def test_create_ticket_uses_service_snapshot() -> None:
    ticket_repo = FakeTicketRepository()
    service_type_repo = FakeServiceTypeRepository()
    service_type_repo.service_types[1] = ServiceType(
        id=1,
        name="Basic Wash",
        desc="Basic exterior wash",
        price=Money(Decimal("50000")),
    )

    result = await CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        FixedBarcodeGenerator(),
    ).execute(CreateTicketCmd(service_type_id=1))

    assert result.id == 1
    assert result.ticket_number == "4006381333931"
    assert result.service_name == "Basic Wash"
    assert result.service_price == Decimal("50000")


@pytest.mark.anyio
async def test_create_ticket_rejects_inactive_service_type() -> None:
    ticket_repo = FakeTicketRepository()
    service_type_repo = FakeServiceTypeRepository()
    service_type_repo.service_types[1] = ServiceType(
        id=1,
        name="Basic Wash",
        desc="Basic exterior wash",
        price=Money(Decimal("50000")),
        is_active=False,
    )

    with pytest.raises(BusinessRuleViolation):
        await CreateTicketUseCase(
            ticket_repo,
            service_type_repo,
            FixedBarcodeGenerator(),
        ).execute(CreateTicketCmd(service_type_id=1))


@pytest.mark.anyio
async def test_list_tickets_applies_filters() -> None:
    ticket_repo = FakeTicketRepository()
    service_type_repo = FakeServiceTypeRepository()
    service_type_repo.service_types[1] = ServiceType(
        id=1,
        name="Basic Wash",
        desc="Basic exterior wash",
        price=Money(Decimal("50000")),
    )
    ticket = await CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        FixedBarcodeGenerator(),
    ).execute(CreateTicketCmd(service_type_id=1))

    result = await ListTicketsUseCase(ticket_repo).execute(
        filters=TicketListFilterDto(
            status=TicketStatusEnum.IN_PROGRESS,
            service_type_id=1,
            ticket_number=ticket.ticket_number,
        )
    )

    assert result.total == 1
    assert result.items[0].id == ticket.id


@pytest.mark.anyio
async def test_void_ticket_marks_ticket_and_creates_void_record() -> None:
    ticket_repo = FakeTicketRepository()
    ticket_void_repo = FakeTicketVoidRepository()
    account_repo = FakeAccountRepository()
    service_type_repo = FakeServiceTypeRepository()
    account_repo.accounts[1] = FakeAccount(id=1)
    service_type_repo.service_types[1] = ServiceType(
        id=1,
        name="Basic Wash",
        desc="Basic exterior wash",
        price=Money(Decimal("50000")),
    )
    ticket = await CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        FixedBarcodeGenerator(),
    ).execute(CreateTicketCmd(service_type_id=1))
    uow = FakeCarwashOperationUnitOfWork(
        ticket_repo,
        ticket_void_repo,
        account_repo,
    )

    result = await VoidTicketUseCase(uow).execute(
        CreateTicketVoidCmd(ticket_id=ticket.id, account_id=1, reason="Wrong service")
    )

    assert result.ticket_id == ticket.id
    assert result.ticket_number == ticket.ticket_number
    assert result.reason == "Wrong service"
    assert ticket_repo.tickets[ticket.id].status == TicketStatusEnum.VOID
    assert uow.committed is True
