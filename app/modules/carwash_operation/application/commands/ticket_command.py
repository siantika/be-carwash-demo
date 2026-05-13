import threading
import time
from dataclasses import dataclass

from app.modules.carwash_operation.application.dto.ticket_dto import (
    CreateTicketCmd,
    TicketResultDto,
)
from app.modules.carwash_operation.application.dto.ticket_mapper import to_ticket_result
from app.modules.carwash_operation.application.dto.ticket_void_dto import (
    CreateTicketVoidCmd,
    TicketVoidResultDto,
)
from app.modules.carwash_operation.application.services.i_barcode_generator import (
    IBarcodeGenerator,
)
from app.modules.carwash_operation.domain.entities.ticket import Ticket
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
    EntityNotFound,
    InactiveServiceTypeCannotBeUsed,
)


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
        return to_ticket_result(created_ticket)


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

