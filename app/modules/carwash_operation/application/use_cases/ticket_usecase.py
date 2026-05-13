import threading
import time
from dataclasses import dataclass

from app.modules.carwash_operation.application.dto.ticket_dto import (
    CreateTicketCmd,
    TicketListResultDto,
    TicketResultDto,
)
from app.modules.carwash_operation.application.dto.ticket_void_dto import (
    CreateTicketVoidCmd,
    TicketVoidResultDto,
)
from app.modules.carwash_operation.application.queries.models import (
    TicketListFilterDto,
)
from app.modules.carwash_operation.application.queries.ticket_query_repository import (
    ITicketQueryRepository,
)
from app.modules.carwash_operation.application.services.i_barcode_generator import (
    IBarcodeGenerator,
)
from app.modules.carwash_operation.domain.entities.ticket import Ticket, TicketStatusEnum
from app.modules.carwash_operation.domain.entities.ticket_void import TicketVoid
from app.modules.carwash_operation.domain.repositories.i_carwash_operation_uow import (
    ICarwashOperationUnitOfWork,
)
from app.modules.carwash_operation.domain.repositories.i_ticket_repo import ITicketRepository
from app.modules.carwash_operation.domain.value_objects.service_snapshot import (
    ServiceSnapshot,
)
from app.modules.carwash_operation.domain.value_objects.ticket_number import TicketNumber
from app.modules.service_catalog.domain.repositories.i_service_type_repo import (
    IServiceTypeRepository,
)
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityNotFound,
    InactiveServiceTypeCannotBeUsed,
)


def _to_ticket_result(ticket: Ticket) -> TicketResultDto:
    return TicketResultDto(
        id=ticket.id,
        ticket_number=ticket.ticket_number.value,
        entry_time=ticket.entry_time.value,
        status=ticket.status.value,
        service_type_id=ticket.service_type_id,
        service_name=ticket.service_snapshot.service_name,
        service_desc=ticket.service_snapshot.service_desc,
        service_price=ticket.service_snapshot.service_price.amount,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def _parse_ticket_status(status: TicketStatusEnum | str | None) -> TicketStatusEnum | None:
    if status is None:
        return None

    if isinstance(status, TicketStatusEnum):
        return status

    try:
        return TicketStatusEnum(status.strip().upper())
    except ValueError as exc:
        raise BusinessRuleViolation("Invalid ticket status") from exc


@dataclass
class GenerateEan13TimeBased:
    node_id: int = 0

    _lock: threading.Lock = threading.Lock()
    _last_ms: int = 0
    _counter: int = 0

    def generate(self) -> str:
        with self._lock:
            now_ms = int(time.time() * 1000)

            if now_ms == self._last_ms:
                self._counter = (self._counter + 1) % 100
            else:
                self._last_ms = now_ms
                self._counter = 0

            time_part = now_ms % 1_000_000_000
            node = int(self.node_id) % 10
            base12 = f"{time_part:09d}{node}{self._counter:02d}"
            return base12 + str(self._checksum(base12))

    @staticmethod
    def _checksum(d12: str) -> int:
        digits = [int(ch) for ch in d12]
        total = sum(digits[0::2]) + 3 * sum(digits[1::2])
        return (10 - (total % 10)) % 10


class CreateTicketUseCase:
    def __init__(
        self,
        ticket_repo: ITicketRepository,
        service_type_repo: IServiceTypeRepository,
        barcode_generator: IBarcodeGenerator,
    ):
        self.ticket_repo = ticket_repo
        self.service_type_repo = service_type_repo
        self.barcode_generator = barcode_generator

    async def execute(self, cmd: CreateTicketCmd) -> TicketResultDto:
        service_type = await self.service_type_repo.find_by_id(cmd.service_type_id)
        if service_type is None:
            raise EntityNotFound("ServiceType", cmd.service_type_id)

        if not service_type.is_active:
            raise InactiveServiceTypeCannotBeUsed(
                "Inactive service type cannot be used for ticket"
            )

        ticket = Ticket(
            service_type_id=service_type.id,
            ticket_number=TicketNumber(self.barcode_generator.generate()),
            service_snapshot=ServiceSnapshot(
                service_name=service_type.name,
                service_price=service_type.price,
                service_desc=service_type.desc,
            ),
        )

        created_ticket = await self.ticket_repo.add(ticket)
        return _to_ticket_result(created_ticket)


class ListTicketsUseCase:
    def __init__(self, ticket_query: ITicketQueryRepository):
        self.ticket_query = ticket_query

    async def execute(
        self,
        filters: TicketListFilterDto | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> TicketListResultDto:
        if page < 1:
            raise BusinessRuleViolation("Page must be greater than or equal to 1")

        if limit < 1:
            raise BusinessRuleViolation("Limit must be greater than or equal to 1")

        filters = filters or TicketListFilterDto()
        status = _parse_ticket_status(filters.status)
        ticket_number = filters.ticket_number.strip() if filters.ticket_number else None
        if ticket_number == "":
            ticket_number = None

        if filters.service_type_id is not None and filters.service_type_id < 1:
            raise BusinessRuleViolation("Service type id must be greater than or equal to 1")

        offset = (page - 1) * limit
        tickets, total = await self.ticket_query.list(
            filters=TicketListFilterDto(
                status=status,
                service_type_id=filters.service_type_id,
                ticket_number=ticket_number,
            ),
            limit=limit,
            offset=offset,
        )

        return TicketListResultDto(
            items=[_to_ticket_result(ticket) for ticket in tickets],
            total=total,
            page=page,
            limit=limit,
        )


class VoidTicketUseCase:
    def __init__(self, uow: ICarwashOperationUnitOfWork):
        self.uow = uow

    async def execute(self, cmd: CreateTicketVoidCmd) -> TicketVoidResultDto:
        async with self.uow as u:
            ticket = await u.ticket.find_by_id(cmd.ticket_id)
            if ticket is None:
                raise EntityNotFound("Ticket", cmd.ticket_id)

            voided_by_account = await u.account.find_by_id(cmd.account_id)
            if voided_by_account is None:
                raise EntityNotFound("Account", cmd.account_id)

            ticket.mark_void()
            await u.ticket.save(ticket)

            ticket_void = await u.ticket_void.add(
                TicketVoid(
                    ticket_id=ticket.id,
                    account_id=cmd.account_id,
                    reason=cmd.reason,
                )
            )
            await u.commit()

        return TicketVoidResultDto(
            id=ticket_void.id,
            ticket_id=ticket_void.ticket_id,
            account_id=ticket_void.account_id,
            ticket_number=ticket.ticket_number.value,
            reason=ticket_void.reason,
            entry_time=ticket.entry_time.value,
            void_time=ticket_void.void_time,
        )
