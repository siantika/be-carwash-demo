import threading
import time
from dataclasses import dataclass

from application.dto.ticket_dto import (
    CreateTicketCmd,
    TicketResultDto,
)
from domain.entities.ticket import Ticket
from domain.exceptions import EntityNotFound
from domain.repositories.i_service_type import IServiceTypeRepository
from domain.repositories.i_ticket_repo import ITicketRepository
from domain.value_object.service_snapshot import ServiceSnapshot
from domain.value_object.ticket_number import TicketNumber
from interfaces.i_barcode_generator import IBarcodeGenerator


@dataclass
class GenerateEan13TimeBased:
    """
    Time-based EAN-13 generator (valid checksum).

    - Produces a 13-digit numeric EAN-13 code with a correct checksum.
    - Uniqueness is probabilistic and is strong for a single process/runtime.

    Notes:
    - This approach is suitable for demos or low-risk use cases.
    - For production systems that require guaranteed uniqueness (especially across
    multiple instances), prefer a persistent sequence/counter (e.g., database
    sequence) or another stateful ID strategy.
    """

    node_id: int = 0  

    _lock: threading.Lock = threading.Lock()
    _last_ms: int = 0
    _counter: int = 0  # 0..99 per ms

    def generate(self) -> str:
        with self._lock:
            now_ms = int(time.time() * 1000)

            if now_ms == self._last_ms:
                self._counter = (self._counter + 1) % 100
            else:
                self._last_ms = now_ms
                self._counter = 0

            # 12 digit base: [9 digit time][1 digit node][2 digit counter]
            # time part pakai modulo agar selalu 9 digit
            time_part = now_ms % 1_000_000_000  # 0..999,999,999 -> 9 digit
            node = int(self.node_id) % 10       # 0..9
            cnt = self._counter                 # 00..99

            base12 = f"{time_part:09d}{node}{cnt:02d}"  # total 12 digit
            check = self._checksum(base12)
            return base12 + str(check)

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
        barcode_generator: IBarcodeGenerator
    ):
        self.ticket_repo = ticket_repo
        self.service_type_repo = service_type_repo
        self.barcode_generator = barcode_generator

    async def execute(self, cmd: CreateTicketCmd) -> TicketResultDto:
        
        service_type = await self.service_type_repo.get_by_id(cmd.service_type_id)
        if not service_type:
            raise EntityNotFound(
                f"Service type with id {cmd.service_type_id} not found"
            )
        
        service_snapshot = ServiceSnapshot(
            service_name= service_type.name,
            service_price= service_type.price,
            service_desc= service_type.desc
        )
        
        ticket = Ticket(
            service_type_id= service_type.id,
            ticket_number= TicketNumber(self.barcode_generator.generate()),
            service_snapshot= service_snapshot,
        )
        
        created_ticket = await self.ticket_repo.add(ticket)
        return TicketResultDto(
            id= created_ticket.id,
            ticket_number= created_ticket.ticket_number,
            entry_time= created_ticket.entry_time,
            status= created_ticket.status,
            service_type_id= created_ticket.service_type_id,
            service_name= created_ticket.service_snapshot.service_name,
            service_desc= created_ticket.service_snapshot.service_desc,
            service_price= created_ticket.service_snapshot.service_price.amount,
            created_at= created_ticket.created_at,
            updated_at= created_ticket.updated_at            
        )