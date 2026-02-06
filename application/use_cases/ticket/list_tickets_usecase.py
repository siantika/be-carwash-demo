
from typing import List

from application.dto.ticket_dto import TicketResultDto
from domain.repositories.i_ticket_repo import ITicketRepository


class ListTicketsUseCase:
    def __init__(
        self,
        ticket_repo:ITicketRepository
    ):
        self.ticket_repo  = ticket_repo 

    async def execute(self, limit:int, offset:int) -> List[TicketResultDto]:
        list_tickets =  await self.ticket_repo.list(limit, offset)
        return [
            TicketResultDto(
                id= ticket.id,
                ticket_number = ticket.ticket_number.value,
                service_type_id= ticket.service_type_id,
                entry_time =ticket.entry_time.value,
                status = ticket.status.value,
                service_name= ticket.service_snapshot.service_name,
                service_desc= ticket.service_snapshot.service_desc,
                service_price= ticket.service_snapshot.service_price.amount,
                created_at= ticket.created_at,
                updated_at= ticket.updated_at
        ) for ticket in list_tickets
            
        ]