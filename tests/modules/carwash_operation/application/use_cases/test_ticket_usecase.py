from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest

from app.modules.carwash_operation.application.dto.ticket_dto import (
    CreateTicketCmd,
)
from app.modules.carwash_operation.application.services.i_request_hasher import IRequestHasher
from app.modules.carwash_operation.application.queries.models import (
    TicketListFilterDto,
)
from app.modules.carwash_operation.application.dto.ticket_void_dto import (
    CreateTicketVoidCmd,
)
from app.modules.carwash_operation.application.commands.ticket_command import (
    CreateTicketUseCase,
    VoidTicketUseCase,
)
from app.modules.carwash_operation.application.queries.ticket_query import ListTicketsUseCase
from app.modules.carwash_operation.domain.entities.idempotency_record import (
    IdempotencyRecord,
)
from app.modules.carwash_operation.domain.entities.ticket import Ticket, TicketStatusEnum
from app.modules.carwash_operation.domain.entities.ticket_void import TicketVoid
from app.modules.service_catalog.domain.entities.service_type import ServiceType
from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    InactiveServiceTypeCannotBeUsed,
)
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
        filters: TicketListFilterDto,
        limit: int,
        offset: int,
    ) -> tuple[list[Ticket], int]:
        tickets = list(self.tickets.values())

        if filters.status is not None:
            tickets = [ticket for ticket in tickets if ticket.status == filters.status]

        if filters.service_type_id is not None:
            tickets = [
                ticket
                for ticket in tickets
                if ticket.service_type_id == filters.service_type_id
            ]

        if filters.ticket_number is not None:
            tickets = [
                ticket
                for ticket in tickets
                if filters.ticket_number in ticket.ticket_number.value
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


class FakeIdempotencyRepository:
    def __init__(self):
        self.records: dict[tuple[str, str], IdempotencyRecord] = {}
        self.next_id = 1

    async def find_by_scope_and_key(
        self,
        *,
        scope: str,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        return self.records.get((scope, idempotency_key))

    async def create_processing(
        self,
        *,
        scope: str,
        idempotency_key: str,
        request_hash: str,
        expires_at,
    ) -> IdempotencyRecord:
        key = (scope, idempotency_key)
        if key in self.records:
            from app.shared.domain.exceptions.exceptions import EntityAlreadyExists

            raise EntityAlreadyExists("IdempotencyKey", idempotency_key)
        now = _utcnow()
        record = IdempotencyRecord(
            id=self.next_id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            status="PROCESSING",
            response_payload=None,
            http_status=None,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )
        self.next_id += 1
        self.records[key] = record
        return record

    async def mark_completed(
        self,
        *,
        record_id: int,
        response_payload: dict,
        http_status: int,
    ) -> IdempotencyRecord:
        for key, record in self.records.items():
            if record.id == record_id:
                updated = IdempotencyRecord(
                    id=record.id,
                    scope=record.scope,
                    idempotency_key=record.idempotency_key,
                    request_hash=record.request_hash,
                    status="COMPLETED",
                    response_payload=response_payload,
                    http_status=http_status,
                    created_at=record.created_at,
                    updated_at=_utcnow(),
                    expires_at=record.expires_at,
                )
                self.records[key] = updated
                return updated
        raise AssertionError("record not found")


class FixedRequestHasher(IRequestHasher):
    def hash(self, payload: dict[str, Any]) -> str:
        return str(payload)


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

    idempotency_repo = FakeIdempotencyRepository()
    result = await CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        FixedBarcodeGenerator(),
        idempotency_repo,
        FixedRequestHasher(),
    ).execute(
        CreateTicketCmd(service_type_id=1),
        idempotency_key="ticket-key-0001",
    )

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

    idempotency_repo = FakeIdempotencyRepository()
    with pytest.raises(InactiveServiceTypeCannotBeUsed):
        await CreateTicketUseCase(
            ticket_repo,
            service_type_repo,
            FixedBarcodeGenerator(),
            idempotency_repo,
            FixedRequestHasher(),
        ).execute(
            CreateTicketCmd(service_type_id=1),
            idempotency_key="ticket-key-0002",
        )


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
    idempotency_repo = FakeIdempotencyRepository()
    ticket = await CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        FixedBarcodeGenerator(),
        idempotency_repo,
        FixedRequestHasher(),
    ).execute(
        CreateTicketCmd(service_type_id=1),
        idempotency_key="ticket-key-0003",
    )

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
    idempotency_repo = FakeIdempotencyRepository()
    ticket = await CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        FixedBarcodeGenerator(),
        idempotency_repo,
        FixedRequestHasher(),
    ).execute(
        CreateTicketCmd(service_type_id=1),
        idempotency_key="ticket-key-0004",
    )
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


@pytest.mark.anyio
async def test_create_ticket_replays_completed_response_for_same_idempotency_key() -> None:
    ticket_repo = FakeTicketRepository()
    service_type_repo = FakeServiceTypeRepository()
    service_type_repo.service_types[1] = ServiceType(
        id=1,
        name="Basic Wash",
        desc="Basic exterior wash",
        price=Money(Decimal("50000")),
    )
    idempotency_repo = FakeIdempotencyRepository()
    usecase = CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        FixedBarcodeGenerator(),
        idempotency_repo,
        FixedRequestHasher(),
    )

    first = await usecase.execute(
        CreateTicketCmd(service_type_id=1),
        idempotency_key="ticket-key-0005",
    )
    second = await usecase.execute(
        CreateTicketCmd(service_type_id=1),
        idempotency_key="ticket-key-0005",
    )

    assert first.id == second.id
    assert len(ticket_repo.tickets) == 1


@pytest.mark.anyio
async def test_create_ticket_rejects_same_idempotency_key_different_payload() -> None:
    ticket_repo = FakeTicketRepository()
    service_type_repo = FakeServiceTypeRepository()
    service_type_repo.service_types[1] = ServiceType(
        id=1,
        name="Basic Wash",
        desc="Basic exterior wash",
        price=Money(Decimal("50000")),
    )
    service_type_repo.service_types[2] = ServiceType(
        id=2,
        name="Premium Wash",
        desc="Premium exterior wash",
        price=Money(Decimal("90000")),
    )
    usecase = CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        FixedBarcodeGenerator(),
        FakeIdempotencyRepository(),
        FixedRequestHasher(),
    )

    await usecase.execute(CreateTicketCmd(service_type_id=1), idempotency_key="ticket-key-0006")
    with pytest.raises(BusinessRuleViolation):
        await usecase.execute(
            CreateTicketCmd(service_type_id=2),
            idempotency_key="ticket-key-0006",
        )
